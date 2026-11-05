import argparse
import base64
import ctypes
import hashlib
import json
import sys
import uuid
from ctypes import wintypes
from datetime import datetime, timezone
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from sqlalchemy.orm import Session as DBSession

from app.auth.models import (
    AdminBootstrapInstanceState,
    AdminBootstrapReceipt,
    User,
    UserRole,
)
from app.auth.policy import Role
from app.config import Settings
from app.database import build_engine


class BootstrapError(Exception):
    """Raised when bootstrap validation or execution fails."""


# ---------------------------------------------------------------------------
# Constants for Windows Registry Trust Boundary (Candidate C)
# ---------------------------------------------------------------------------
MAX_STDIN_BYTES = 65536  # 64 KB bounded stdin payload

if ctypes.sizeof(ctypes.c_void_p) == 8:
    HKEY_LOCAL_MACHINE = 0xFFFFFFFF80000002
else:
    HKEY_LOCAL_MACHINE = 0x80000002

KEY_QUERY_VALUE = 0x0001
KEY_SET_VALUE = 0x0002
KEY_CREATE_SUB_KEY = 0x0004
KEY_CREATE_LINK = 0x0020
KEY_WOW64_64KEY = 0x0100
DELETE = 0x00010000
READ_CONTROL = 0x00020000
WRITE_DAC = 0x00040000
WRITE_OWNER = 0x00080000
KEY_READ = 0x20019
KEY_WRITE = 0x20006
KEY_EXECUTE = 0x20019
KEY_ALL_ACCESS = 0xF003F

REG_BINARY = 3

TOKEN_QUERY = 0x0008
TOKEN_DUPLICATE = 0x0002
SecurityImpersonation = 2

OWNER_SECURITY_INFORMATION = 0x00000001
GROUP_SECURITY_INFORMATION = 0x00000002
DACL_SECURITY_INFORMATION = 0x00000004
SE_DACL_PRESENT = 0x0004
SE_DACL_PROTECTED = 0x1000

SE_REGISTRY_KEY = 4
ACCESS_ALLOWED_ACE_TYPE = 0x00
ACCESS_DENIED_ACE_TYPE = 0x01
INHERITED_ACE = 0x10
AclSizeInformation = 2

SID_BUILTIN_ADMINISTRATORS = "S-1-5-32-544"
SID_LOCAL_SYSTEM = "S-1-5-18"
SID_BUILTIN_USERS = "S-1-5-32-545"
APPROVED_TASK_KEY_SDDL = "O:BA G:SY D:P(A;;KA;;;SY)(A;;KA;;;BA)(A;;KR;;;BU)"

PROHIBITED_RIGHTS = (
    KEY_SET_VALUE | KEY_CREATE_SUB_KEY | KEY_CREATE_LINK | DELETE | WRITE_DAC | WRITE_OWNER
)

REGISTRY_HIVE = "HKLM"
REGISTRY_ROOT_PATH = "SOFTWARE"
REGISTRY_NAMESPACE_PATH = r"SOFTWARE\CHPMIS011LocalSynthetic"
REGISTRY_TRUST_KEY_PATH = r"SOFTWARE\CHPMIS011LocalSynthetic\TrustedApprovers"

VAL_PROJECT_OWNER = "ProjectOwnerEd25519PublicKey"
VAL_SECURITY_REVIEWER = "SecurityReviewerEd25519PublicKey"
EXPECTED_VALUE_NAMES = {VAL_PROJECT_OWNER, VAL_SECURITY_REVIEWER}


# ---------------------------------------------------------------------------
# Windows Ctypes Definitions for AccessCheck and Registry inspection
# ---------------------------------------------------------------------------
if sys.platform == "win32":

    class GENERIC_MAPPING(ctypes.Structure):
        _fields_ = [
            ("GenericRead", wintypes.DWORD),
            ("GenericWrite", wintypes.DWORD),
            ("GenericExecute", wintypes.DWORD),
            ("GenericAll", wintypes.DWORD),
        ]

    class PRIVILEGE_SET(ctypes.Structure):
        _fields_ = [
            ("PrivilegeCount", wintypes.DWORD),
            ("Control", wintypes.DWORD),
            ("Privilege", wintypes.DWORD * 3),
        ]

    class ACL_SIZE_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("AceCount", wintypes.DWORD),
            ("AclBytesInUse", wintypes.DWORD),
            ("AclBytesFree", wintypes.DWORD),
        ]

    class ACE_HEADER(ctypes.Structure):
        _fields_ = [
            ("AceType", wintypes.BYTE),
            ("AceFlags", wintypes.BYTE),
            ("AceSize", wintypes.WORD),
        ]

    class ACCESS_ALLOWED_ACE(ctypes.Structure):
        _fields_ = [
            ("Header", ACE_HEADER),
            ("Mask", wintypes.DWORD),
            ("SidStart", wintypes.DWORD),
        ]


def configure_win32_prototypes(advapi32=None, kernel32=None) -> None:
    """Explicitly configure argtypes and restype on Win32 DLL functions."""
    if sys.platform != "win32":
        return

    if advapi32 is None:
        advapi32 = ctypes.windll.advapi32
    if kernel32 is None:
        kernel32 = ctypes.windll.kernel32

    # kernel32
    kernel32.GetCurrentProcess.argtypes = []
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE

    kernel32.GetLastError.argtypes = []
    kernel32.GetLastError.restype = wintypes.DWORD

    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p

    # advapi32
    advapi32.OpenProcessToken.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.HANDLE),
    ]
    advapi32.OpenProcessToken.restype = wintypes.BOOL

    advapi32.DuplicateToken.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.HANDLE),
    ]
    advapi32.DuplicateToken.restype = wintypes.BOOL

    advapi32.RegOpenKeyExW.argtypes = [
        wintypes.HKEY,
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.HKEY),
    ]
    advapi32.RegOpenKeyExW.restype = wintypes.LONG

    advapi32.RegCloseKey.argtypes = [wintypes.HKEY]
    advapi32.RegCloseKey.restype = wintypes.LONG

    advapi32.GetSecurityInfo.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_void_p),
    ]
    advapi32.GetSecurityInfo.restype = wintypes.DWORD

    advapi32.GetSecurityDescriptorControl.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(wintypes.WORD),
        ctypes.POINTER(wintypes.DWORD),
    ]
    advapi32.GetSecurityDescriptorControl.restype = wintypes.BOOL

    advapi32.GetSecurityDescriptorOwner.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(wintypes.BOOL),
    ]
    advapi32.GetSecurityDescriptorOwner.restype = wintypes.BOOL

    advapi32.GetSecurityDescriptorDacl.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(wintypes.BOOL),
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(wintypes.BOOL),
    ]
    advapi32.GetSecurityDescriptorDacl.restype = wintypes.BOOL

    advapi32.GetAclInformation.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
    ]
    advapi32.GetAclInformation.restype = wintypes.BOOL

    advapi32.GetAce.argtypes = [
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    advapi32.GetAce.restype = wintypes.BOOL

    advapi32.ConvertSidToStringSidW.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(wintypes.LPWSTR),
    ]
    advapi32.ConvertSidToStringSidW.restype = wintypes.BOOL

    advapi32.MapGenericMask.argtypes = [
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(GENERIC_MAPPING),
    ]
    advapi32.MapGenericMask.restype = None

    advapi32.AccessCheck.argtypes = [
        ctypes.c_void_p,
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.POINTER(GENERIC_MAPPING),
        ctypes.POINTER(PRIVILEGE_SET),
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.BOOL),
    ]
    advapi32.AccessCheck.restype = wintypes.BOOL

    advapi32.RegQueryInfoKeyW.argtypes = [
        wintypes.HKEY,
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD),
        ctypes.c_void_p,
    ]
    advapi32.RegQueryInfoKeyW.restype = wintypes.LONG

    advapi32.RegEnumValueW.argtypes = [
        wintypes.HKEY,
        wintypes.DWORD,
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD),
        ctypes.c_void_p,
        ctypes.POINTER(wintypes.DWORD),
    ]
    advapi32.RegEnumValueW.restype = wintypes.LONG


if sys.platform == "win32":
    configure_win32_prototypes()


def parse_sddl(sddl: str) -> tuple[str | None, bool, list[dict[str, Any]]]:
    """Parse standard SDDL subset for task keys into (owner_sid, dacl_protected, aces)."""
    import re

    owner_m = re.search(r"O:([A-Za-z0-9-]+)", sddl)
    owner = None
    if owner_m:
        raw_owner = owner_m.group(1)
        if raw_owner == "BA":
            owner = SID_BUILTIN_ADMINISTRATORS
        elif raw_owner == "SY":
            owner = SID_LOCAL_SYSTEM
        elif raw_owner == "BU":
            owner = SID_BUILTIN_USERS
        else:
            owner = raw_owner

    dacl_m = re.search(r"D:([P]?)", sddl)
    dacl_protected = bool(dacl_m and "P" in dacl_m.group(1))

    ace_matches = re.findall(r"\(([A-Za-z0-9;_-]+)\)", sddl)
    aces = []
    for raw_ace in ace_matches:
        parts = raw_ace.split(";")
        if len(parts) >= 6:
            ace_type_code, ace_flags_code, ace_perms, _, _, ace_trustee = parts[:6]
            ace_type = (
                "ACCESS_ALLOWED"
                if ace_type_code == "A"
                else ("ACCESS_DENIED" if ace_type_code == "D" else ace_type_code)
            )
            flags = 0
            if ace_flags_code == "IN":
                flags = INHERITED_ACE
            elif ace_flags_code:
                try:
                    flags = int(ace_flags_code, 16)
                except ValueError:
                    flags = 1

            if ace_perms == "KA":
                mask = KEY_ALL_ACCESS
            elif ace_perms == "KR":
                mask = KEY_READ
            elif ace_perms == "KW":
                mask = KEY_WRITE
            else:
                try:
                    mask = int(ace_perms, 16)
                except ValueError:
                    mask = 0

            trustee = ace_trustee
            if trustee == "SY":
                trustee = SID_LOCAL_SYSTEM
            elif trustee == "BA":
                trustee = SID_BUILTIN_ADMINISTRATORS
            elif trustee == "BU":
                trustee = SID_BUILTIN_USERS

            aces.append(
                {
                    "type": ace_type,
                    "flags": flags,
                    "mask": mask,
                    "trustee_sid": trustee,
                }
            )
    return owner, dacl_protected, aces


class WindowsRegistryBackend:
    """Production reader for the fixed 64-bit HKLM trust boundary via Windows APIs."""

    def __init__(self, advapi32=None, kernel32=None):
        self._advapi32 = advapi32
        self._kernel32 = kernel32

    def is_windows(self) -> bool:
        return sys.platform == "win32"

    def read_trusted_keys(self) -> dict[str, bytes]:
        if not self.is_windows():
            raise BootstrapError(
                "Registry trust boundary is supported only on Windows (win32); "
                "execution on non-Windows platforms is rejected."
            )

        advapi32 = self._advapi32 if self._advapi32 is not None else ctypes.windll.advapi32
        kernel32 = self._kernel32 if self._kernel32 is not None else ctypes.windll.kernel32
        configure_win32_prototypes(advapi32, kernel32)

        # 1. Obtain impersonation token duplicated from current process primary token
        h_process_token = wintypes.HANDLE()
        h_impersonation_token = wintypes.HANDLE()

        current_process = kernel32.GetCurrentProcess()
        if not advapi32.OpenProcessToken(
            current_process,
            TOKEN_DUPLICATE | TOKEN_QUERY,
            ctypes.byref(h_process_token),
        ):
            err = kernel32.GetLastError()
            raise BootstrapError(
                f"Failed to open process token for trust verification (error {err})"
            )

        try:
            if not advapi32.DuplicateToken(
                h_process_token,
                SecurityImpersonation,
                ctypes.byref(h_impersonation_token),
            ):
                err = kernel32.GetLastError()
                raise BootstrapError(
                    f"Failed to duplicate process token at SecurityImpersonation (error {err})"
                )
        finally:
            kernel32.CloseHandle(h_process_token)

        # 2. Setup generic mapping for registry objects
        generic_mapping = GENERIC_MAPPING()
        generic_mapping.GenericRead = KEY_READ
        generic_mapping.GenericWrite = KEY_WRITE
        generic_mapping.GenericExecute = KEY_EXECUTE
        generic_mapping.GenericAll = KEY_ALL_ACCESS

        # 3. Path components to verify in order:
        # Ancestors: SOFTWARE, SOFTWARE\CHPMIS011LocalSynthetic
        # Leaf: SOFTWARE\CHPMIS011LocalSynthetic\TrustedApprovers
        path_components = [
            (REGISTRY_ROOT_PATH, False),
            (REGISTRY_NAMESPACE_PATH, True),
            (REGISTRY_TRUST_KEY_PATH, True),
        ]

        handles_to_close: list[Any] = []
        try:
            for subkey_path, is_task_created in path_components:
                h_key = wintypes.HKEY()
                # Open with explicit ulOptions=0 and KEY_WOW64_64KEY
                sam_desired = KEY_READ | KEY_WOW64_64KEY
                ret = advapi32.RegOpenKeyExW(
                    HKEY_LOCAL_MACHINE,
                    subkey_path,
                    0,  # ulOptions=0
                    sam_desired,
                    ctypes.byref(h_key),
                )
                if ret != 0:
                    raise BootstrapError(
                        f"Failed to open fixed registry key '{subkey_path}' "
                        f"in 64-bit view (error {ret})"
                    )
                handles_to_close.append(h_key)

                # Query security descriptor
                p_sd = ctypes.c_void_p()
                sec_info = OWNER_SECURITY_INFORMATION | DACL_SECURITY_INFORMATION
                ret = advapi32.GetSecurityInfo(
                    h_key,
                    SE_REGISTRY_KEY,
                    sec_info,
                    None,
                    None,
                    None,
                    None,
                    ctypes.byref(p_sd),
                )
                if ret != 0:
                    raise BootstrapError(
                        f"Failed to get security descriptor for key '{subkey_path}' (error {ret})"
                    )

                try:
                    # Validate DACL presence and protection
                    control = wintypes.WORD()
                    revision = wintypes.DWORD()
                    if not advapi32.GetSecurityDescriptorControl(
                        p_sd, ctypes.byref(control), ctypes.byref(revision)
                    ):
                        err = kernel32.GetLastError()
                        raise BootstrapError(
                            f"Failed to get security descriptor control for '{subkey_path}' "
                            f"(error {err})"
                        )

                    c_val = control.value
                    if not (c_val & SE_DACL_PRESENT):
                        raise BootstrapError(
                            f"Registry key '{subkey_path}' has no DACL; fail closed."
                        )

                    if is_task_created and not (c_val & SE_DACL_PROTECTED):
                        raise BootstrapError(
                            f"Task-created registry key '{subkey_path}' does not have "
                            "protected DACL; fail closed."
                        )

                    # Task-created keys require Owner SID and exact DACL/ACE validation
                    if is_task_created:
                        # Validate Owner SID: BUILTIN\Administrators (S-1-5-32-544)
                        p_owner = ctypes.c_void_p()
                        owner_defaulted = wintypes.BOOL()
                        if (
                            not advapi32.GetSecurityDescriptorOwner(
                                p_sd, ctypes.byref(p_owner), ctypes.byref(owner_defaulted)
                            )
                            or not p_owner
                        ):
                            raise BootstrapError(
                                "Failed to extract owner SID from security descriptor for "
                                f"'{subkey_path}'; fail closed."
                            )
                        p_owner_str = wintypes.LPWSTR()
                        if (
                            not advapi32.ConvertSidToStringSidW(p_owner, ctypes.byref(p_owner_str))
                            or not p_owner_str
                        ):
                            raise BootstrapError(
                                f"Failed to convert owner SID to string for '{subkey_path}'; "
                                "fail closed."
                            )
                        try:
                            owner_sid_val = p_owner_str.value
                            if owner_sid_val != SID_BUILTIN_ADMINISTRATORS:
                                raise BootstrapError(
                                    f"Task-created registry key '{subkey_path}' owner SID must be "
                                    f"BUILTIN\\Administrators ({SID_BUILTIN_ADMINISTRATORS}); "
                                    f"found '{owner_sid_val}'."
                                )
                        finally:
                            kernel32.LocalFree(p_owner_str)

                        # Validate DACL and exact ACEs
                        dacl_present = wintypes.BOOL()
                        p_dacl = ctypes.c_void_p()
                        dacl_defaulted = wintypes.BOOL()
                        if (
                            not advapi32.GetSecurityDescriptorDacl(
                                p_sd,
                                ctypes.byref(dacl_present),
                                ctypes.byref(p_dacl),
                                ctypes.byref(dacl_defaulted),
                            )
                            or not dacl_present.value
                            or not p_dacl
                        ):
                            raise BootstrapError(
                                f"Failed to get DACL for '{subkey_path}'; fail closed."
                            )

                        acl_size = ACL_SIZE_INFORMATION()
                        if not advapi32.GetAclInformation(
                            p_dacl,
                            ctypes.byref(acl_size),
                            ctypes.sizeof(acl_size),
                            AclSizeInformation,
                        ):
                            raise BootstrapError(
                                f"Failed to get ACL information for '{subkey_path}'; fail closed."
                            )

                        if acl_size.AceCount != 3:
                            raise BootstrapError(
                                f"Task-created registry key '{subkey_path}' DACL must have "
                                f"exactly 3 ACEs; found {acl_size.AceCount}."
                            )

                        expected_ace_specs = {
                            SID_LOCAL_SYSTEM: KEY_ALL_ACCESS,
                            SID_BUILTIN_ADMINISTRATORS: KEY_ALL_ACCESS,
                            SID_BUILTIN_USERS: KEY_READ,
                        }
                        found_trustees = set()
                        for idx in range(acl_size.AceCount):
                            p_ace = ctypes.c_void_p()
                            if (
                                not advapi32.GetAce(p_dacl, idx, ctypes.byref(p_ace))
                                or not p_ace
                                or p_ace.value is None
                            ):
                                raise BootstrapError(
                                    f"Failed to get ACE {idx} for '{subkey_path}'; fail closed."
                                )
                            ace_addr = p_ace.value
                            header = ACE_HEADER.from_address(ace_addr)
                            if header.AceType != ACCESS_ALLOWED_ACE_TYPE:
                                raise BootstrapError(
                                    f"Unexpected ACE type {header.AceType} in DACL for "
                                    f"'{subkey_path}'; only ACCESS_ALLOWED ACEs permitted."
                                )
                            if header.AceFlags != 0:
                                raise BootstrapError(
                                    f"Unexpected ACE flags {header.AceFlags} in DACL for "
                                    f"'{subkey_path}'; inherited or non-zero ACE flags rejected."
                                )
                            allowed_ace = ACCESS_ALLOWED_ACE.from_address(ace_addr)
                            sid_offset = ctypes.sizeof(ACE_HEADER) + ctypes.sizeof(wintypes.DWORD)
                            sid_ptr = ctypes.c_void_p(ace_addr + sid_offset)
                            p_ace_sid_str = wintypes.LPWSTR()
                            if (
                                not advapi32.ConvertSidToStringSidW(
                                    sid_ptr, ctypes.byref(p_ace_sid_str)
                                )
                                or not p_ace_sid_str
                            ):
                                raise BootstrapError(
                                    f"Failed to convert ACE SID to string for '{subkey_path}'; "
                                    "fail closed."
                                )
                            try:
                                sid_str = p_ace_sid_str.value
                            finally:
                                kernel32.LocalFree(p_ace_sid_str)

                            if sid_str not in expected_ace_specs:
                                raise BootstrapError(
                                    f"Unexpected trustee SID '{sid_str}' in DACL for "
                                    f"'{subkey_path}'."
                                )
                            if sid_str in found_trustees:
                                raise BootstrapError(
                                    f"Duplicate trustee SID '{sid_str}' in DACL for "
                                    f"'{subkey_path}'."
                                )
                            found_trustees.add(sid_str)

                            if allowed_ace.Mask != expected_ace_specs[sid_str]:
                                raise BootstrapError(
                                    f"Incorrect access mask {hex(allowed_ace.Mask)} for trustee "
                                    f"'{sid_str}' in '{subkey_path}'; "
                                    f"expected {hex(expected_ace_specs[sid_str])}."
                                )

                    # AccessCheck against duplicated impersonation token for prohibited rights
                    for prohibited_mask, right_name in [
                        (KEY_SET_VALUE, "KEY_SET_VALUE"),
                        (KEY_CREATE_SUB_KEY, "KEY_CREATE_SUB_KEY"),
                        (KEY_CREATE_LINK, "KEY_CREATE_LINK"),
                        (DELETE, "DELETE"),
                        (WRITE_DAC, "WRITE_DAC"),
                        (WRITE_OWNER, "WRITE_OWNER"),
                        (KEY_WRITE, "KEY_WRITE"),
                        (KEY_ALL_ACCESS, "KEY_ALL_ACCESS"),
                    ]:
                        desired_access = wintypes.DWORD(prohibited_mask)
                        advapi32.MapGenericMask(
                            ctypes.byref(desired_access), ctypes.byref(generic_mapping)
                        )
                        privilege_set = PRIVILEGE_SET()
                        priv_len = wintypes.DWORD(ctypes.sizeof(privilege_set))
                        granted_access = wintypes.DWORD(0)
                        access_status = wintypes.BOOL(0)

                        if not advapi32.AccessCheck(
                            p_sd,
                            h_impersonation_token,
                            desired_access,
                            ctypes.byref(generic_mapping),
                            ctypes.byref(privilege_set),
                            ctypes.byref(priv_len),
                            ctypes.byref(granted_access),
                            ctypes.byref(access_status),
                        ):
                            err = kernel32.GetLastError()
                            raise BootstrapError(
                                f"AccessCheck failed for right {right_name} on "
                                f"'{subkey_path}' (error {err})"
                            )

                        if access_status.value != 0:
                            raise BootstrapError(
                                f"Operator token has prohibited right {right_name} "
                                f"on '{subkey_path}'; trust boundary violation rejected."
                            )
                finally:
                    kernel32.LocalFree(p_sd)

            # 4. Enumerate and validate exact values on the leaf key (handles_to_close[-1])
            leaf_key = handles_to_close[-1]
            c_values = wintypes.DWORD()
            ret = advapi32.RegQueryInfoKeyW(
                leaf_key,
                None,
                None,
                None,
                None,
                None,
                None,
                ctypes.byref(c_values),
                None,
                None,
                None,
                None,
            )
            if ret != 0:
                raise BootstrapError(f"RegQueryInfoKeyW failed on trust key (error {ret})")

            if c_values.value != 2:
                raise BootstrapError(
                    f"Trust key must contain exactly 2 values; found {c_values.value}."
                )

            keys_read: dict[str, bytes] = {}
            for idx in range(2):
                val_name_buf = ctypes.create_unicode_buffer(256)
                cch_val_name = wintypes.DWORD(256)
                val_type = wintypes.DWORD()
                data_buf = (ctypes.c_ubyte * 256)()
                cb_data = wintypes.DWORD(256)

                ret = advapi32.RegEnumValueW(
                    leaf_key,
                    idx,
                    val_name_buf,
                    ctypes.byref(cch_val_name),
                    None,
                    ctypes.byref(val_type),
                    ctypes.cast(data_buf, ctypes.c_void_p),
                    ctypes.byref(cb_data),
                )
                if ret != 0:
                    raise BootstrapError(f"RegEnumValueW failed for index {idx} (error {ret})")

                val_name = val_name_buf.value
                if val_name not in EXPECTED_VALUE_NAMES:
                    raise BootstrapError(f"Unexpected value name '{val_name}' in trust key.")
                if val_type.value != REG_BINARY:
                    raise BootstrapError(
                        f"Value '{val_name}' must be of type REG_BINARY ({REG_BINARY}); "
                        f"found {val_type.value}."
                    )
                if cb_data.value != 32:
                    raise BootstrapError(
                        f"Value '{val_name}' must be exactly 32 bytes; found {cb_data.value}."
                    )

                raw_bytes = bytes(data_buf[: cb_data.value])
                keys_read[val_name] = raw_bytes

            if len(keys_read) != 2:
                raise BootstrapError("Failed to read both expected public keys.")

            po_bytes = keys_read[VAL_PROJECT_OWNER]
            sr_bytes = keys_read[VAL_SECURITY_REVIEWER]
            if po_bytes == sr_bytes:
                raise BootstrapError(
                    "Project Owner and Security Reviewer approver keys must be distinct; "
                    "same-person approval rejected."
                )

            return {
                "project_owner": po_bytes,
                "security_reviewer": sr_bytes,
            }
        finally:
            for hk in handles_to_close:
                advapi32.RegCloseKey(hk)
            kernel32.CloseHandle(h_impersonation_token)


# ---------------------------------------------------------------------------
# Synthetic In-Memory Registry Test Seam Fixture
# ---------------------------------------------------------------------------
class SyntheticRegistryBackend:
    """In-memory synthetic registry fixture simulating Windows 64-bit Registry APIs."""

    def __init__(
        self,
        *,
        is_windows: bool = True,
        keys: dict[str, dict[str, Any]] | None = None,
        token_duplicate_fails: bool = False,
        api_error: Exception | None = None,
        default_acls: bool = True,
    ):
        self._is_windows = is_windows
        self.token_duplicate_fails = token_duplicate_fails
        self.api_error = api_error

        if keys is None:
            self.keys = {}
        else:
            self.keys = keys
            if default_acls:
                for subkey_path in (REGISTRY_NAMESPACE_PATH, REGISTRY_TRUST_KEY_PATH):
                    if subkey_path in self.keys:
                        k_entry = self.keys[subkey_path]
                        if "owner_sid" not in k_entry and "sddl" not in k_entry:
                            k_entry["owner_sid"] = SID_BUILTIN_ADMINISTRATORS
                        if "dacl_aces" not in k_entry and "sddl" not in k_entry:
                            k_entry["dacl_aces"] = [
                                {
                                    "type": "ACCESS_ALLOWED",
                                    "flags": 0,
                                    "mask": KEY_ALL_ACCESS,
                                    "trustee_sid": SID_LOCAL_SYSTEM,
                                },
                                {
                                    "type": "ACCESS_ALLOWED",
                                    "flags": 0,
                                    "mask": KEY_ALL_ACCESS,
                                    "trustee_sid": SID_BUILTIN_ADMINISTRATORS,
                                },
                                {
                                    "type": "ACCESS_ALLOWED",
                                    "flags": 0,
                                    "mask": KEY_READ,
                                    "trustee_sid": SID_BUILTIN_USERS,
                                },
                            ]
                            k_entry["sddl"] = APPROVED_TASK_KEY_SDDL

    def is_windows(self) -> bool:
        return self._is_windows

    def read_trusted_keys(self) -> dict[str, bytes]:
        if not self.is_windows():
            raise BootstrapError(
                "Registry trust boundary is supported only on Windows (win32); "
                "execution on non-Windows platforms is rejected."
            )

        if self.api_error is not None:
            raise self.api_error

        if self.token_duplicate_fails:
            raise BootstrapError(
                "Failed to duplicate process token at SecurityImpersonation (simulated error)"
            )

        path_components = [
            (REGISTRY_ROOT_PATH, False),
            (REGISTRY_NAMESPACE_PATH, True),
            (REGISTRY_TRUST_KEY_PATH, True),
        ]

        for subkey_path, is_task_created in path_components:
            if subkey_path not in self.keys:
                raise BootstrapError(
                    f"Failed to open fixed registry key '{subkey_path}' in 64-bit view: "
                    "key not found"
                )

            k_info = self.keys[subkey_path]

            # DACL presence and protection check
            dacl_present = k_info.get("dacl_present", True)
            if not dacl_present:
                raise BootstrapError(f"Registry key '{subkey_path}' has no DACL; fail closed.")

            dacl_protected = k_info.get("dacl_protected", True if is_task_created else False)
            if is_task_created and not dacl_protected:
                raise BootstrapError(
                    f"Task-created registry key '{subkey_path}' does not have "
                    "protected DACL; fail closed."
                )

            # Task-created keys require Owner SID and exact DACL/ACE validation
            if is_task_created:
                # 1. Owner SID validation
                owner_sid = k_info.get("owner_sid")
                sddl_str = k_info.get("sddl")
                if owner_sid is None and sddl_str:
                    sddl_owner, _, _ = parse_sddl(sddl_str)
                    owner_sid = sddl_owner

                if owner_sid is None:
                    raise BootstrapError(
                        f"Task-created registry key '{subkey_path}' has no owner SID evidence; "
                        "fail closed."
                    )
                if owner_sid != SID_BUILTIN_ADMINISTRATORS:
                    raise BootstrapError(
                        f"Task-created registry key '{subkey_path}' owner SID must be "
                        f"BUILTIN\\Administrators ({SID_BUILTIN_ADMINISTRATORS}); "
                        f"found '{owner_sid}'."
                    )

                # 2. DACL / ACE validation
                aces = k_info.get("dacl_aces")
                if aces is None and sddl_str:
                    _, _, sddl_aces = parse_sddl(sddl_str)
                    aces = sddl_aces

                if aces is None:
                    raise BootstrapError(
                        f"Task-created registry key '{subkey_path}' has no DACL/ACE evidence; "
                        "fail closed."
                    )

                if len(aces) != 3:
                    raise BootstrapError(
                        f"Task-created registry key '{subkey_path}' DACL must have "
                        f"exactly 3 ACEs; found {len(aces)}."
                    )

                expected_aces = {
                    SID_LOCAL_SYSTEM: KEY_ALL_ACCESS,
                    SID_BUILTIN_ADMINISTRATORS: KEY_ALL_ACCESS,
                    SID_BUILTIN_USERS: KEY_READ,
                }
                found_trustees = set()
                for ace in aces:
                    ace_type = ace.get("type")
                    if ace_type not in ("ACCESS_ALLOWED", ACCESS_ALLOWED_ACE_TYPE, 0):
                        raise BootstrapError(
                            f"Unexpected ACE type '{ace_type}' in DACL for '{subkey_path}'; "
                            "only ACCESS_ALLOWED permitted."
                        )
                    flags = ace.get("flags", 0)
                    if flags != 0:
                        raise BootstrapError(
                            f"Unexpected ACE flags {flags} in DACL for '{subkey_path}'; "
                            "inherited or non-zero flags rejected."
                        )
                    trustee = ace.get("trustee_sid")
                    if trustee not in expected_aces:
                        raise BootstrapError(
                            f"Unexpected trustee SID '{trustee}' in DACL for '{subkey_path}'."
                        )
                    if trustee in found_trustees:
                        raise BootstrapError(
                            f"Duplicate trustee SID '{trustee}' in DACL for '{subkey_path}'."
                        )
                    found_trustees.add(trustee)

                    mask = ace.get("mask")
                    if mask != expected_aces[trustee]:
                        raise BootstrapError(
                            f"Incorrect access mask {hex(mask) if isinstance(mask, int) else mask} "
                            f"for trustee '{trustee}' in '{subkey_path}'; "
                            f"expected {hex(expected_aces[trustee])}."
                        )

            # Prohibited rights check via AccessCheck simulation
            if k_info.get("prohibited_rights_granted", False):
                raise BootstrapError(
                    f"Operator token has prohibited rights on '{subkey_path}'; "
                    f"trust boundary violation rejected."
                )

            access_check_error = k_info.get("access_check_error")
            if access_check_error:
                raise BootstrapError(f"AccessCheck failed on '{subkey_path}': {access_check_error}")

        # Leaf inspection
        leaf_info = self.keys[REGISTRY_TRUST_KEY_PATH]
        values = leaf_info.get("values", {})

        if len(values) != 2:
            raise BootstrapError(f"Trust key must contain exactly 2 values; found {len(values)}.")

        val_names = set(values.keys())
        if val_names != EXPECTED_VALUE_NAMES:
            raise BootstrapError(
                f"Unexpected value names {val_names} in trust key; expected {EXPECTED_VALUE_NAMES}."
            )

        keys_read: dict[str, bytes] = {}
        for name, val_entry in values.items():
            val_type, val_data = val_entry
            if val_type != REG_BINARY:
                raise BootstrapError(
                    f"Value '{name}' must be of type REG_BINARY ({REG_BINARY}); found {val_type}."
                )
            if not isinstance(val_data, bytes) or len(val_data) != 32:
                length = len(val_data) if isinstance(val_data, bytes) else "non-bytes"
                raise BootstrapError(f"Value '{name}' must be exactly 32 bytes; found {length}.")
            keys_read[name] = val_data

        po_bytes = keys_read[VAL_PROJECT_OWNER]
        sr_bytes = keys_read[VAL_SECURITY_REVIEWER]
        if po_bytes == sr_bytes:
            raise BootstrapError(
                "Project Owner and Security Reviewer approver keys must be distinct; "
                "same-person approval rejected."
            )

        return {
            "project_owner": po_bytes,
            "security_reviewer": sr_bytes,
        }


# Global active backend test seam
_ACTIVE_REGISTRY_BACKEND: Any = None


def set_test_registry_backend(backend: Any) -> None:
    """Internal test seam: set the synthetic in-memory registry backend."""
    global _ACTIVE_REGISTRY_BACKEND
    _ACTIVE_REGISTRY_BACKEND = backend


def load_trusted_approver_keys(_backend: Any = None) -> dict[str, bytes]:
    """Load trusted approver keys from the fixed 64-bit HKLM trust boundary."""
    backend = _backend or _ACTIVE_REGISTRY_BACKEND or WindowsRegistryBackend()
    return backend.read_trusted_keys()


# ---------------------------------------------------------------------------
# Instance State, Canonical Payload, and Parsing
# ---------------------------------------------------------------------------
def get_or_create_instance_state(db: DBSession) -> AdminBootstrapInstanceState:
    """Retrieve or initialize the persistent singleton instance UUID for this database."""
    state = db.query(AdminBootstrapInstanceState).first()
    if state is not None:
        return state

    new_instance_id = str(uuid.uuid4())
    state = AdminBootstrapInstanceState(
        instance_id=new_instance_id,
        singleton_lock="INSTANCE_LOCK",
    )
    db.add(state)
    db.commit()
    db.refresh(state)
    return state


def parse_iso_utc(val: str) -> datetime:
    """Parse an ISO 8601 UTC timestamp and enforce zero-skew UTC timezone."""
    if not isinstance(val, str):
        raise BootstrapError("Timestamp must be an ISO 8601 string")

    normalized = val.strip()
    if not (normalized.endswith("Z") or normalized.endswith("+00:00")):
        raise BootstrapError(
            f"Timestamp '{val}' must be in explicit UTC format ending in 'Z' or '+00:00'"
        )

    try:
        iso_str = normalized[:-1] + "+00:00" if normalized.endswith("Z") else normalized
        dt = datetime.fromisoformat(iso_str)
    except Exception as exc:
        raise BootstrapError(f"Malformed ISO 8601 timestamp '{val}': {exc}") from exc

    if dt.tzinfo is None:
        raise BootstrapError(f"Timestamp '{val}' lacks timezone information")

    return dt.astimezone(timezone.utc)


def format_iso_utc(dt: datetime) -> str:
    """Format a datetime into canonical UTC ISO 8601 string ending in Z."""
    utc_dt = dt.astimezone(timezone.utc)
    return (
        utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        if utc_dt.microsecond == 0
        else utc_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    )


def create_canonical_payload(
    environment: str,
    target_subs: list[str],
    *,
    instance_id: str | None = None,
    request_id: str | None = None,
    operator_id: str | None = None,
    issued_at: str | datetime | None = None,
    expires_at: str | datetime | None = None,
) -> bytes:
    """Create the canonical JSON payload binding action, env, targets, and optionally W9 fields."""
    if len(target_subs) != 2:
        raise BootstrapError("Bootstrap requires exactly two target users")
    if target_subs[0] == target_subs[1]:
        raise BootstrapError("Bootstrap target users must be distinct")

    if (
        instance_id is not None
        or request_id is not None
        or operator_id is not None
        or issued_at is not None
        or expires_at is not None
    ):
        if not instance_id or not isinstance(instance_id, str):
            raise BootstrapError("instance_id must be a non-empty string")
        if not request_id or not isinstance(request_id, str):
            raise BootstrapError("request_id must be a non-empty string")
        if not operator_id or not isinstance(operator_id, str):
            raise BootstrapError("operator_id must be a non-empty string")
        if issued_at is None:
            raise BootstrapError("issued_at is required for hardened payload")
        if expires_at is None:
            raise BootstrapError("expires_at is required for hardened payload")

        issued_dt = (
            parse_iso_utc(issued_at)
            if isinstance(issued_at, str)
            else issued_at.astimezone(timezone.utc)
        )
        expires_dt = (
            parse_iso_utc(expires_at)
            if isinstance(expires_at, str)
            else expires_at.astimezone(timezone.utc)
        )

        validity_seconds = (expires_dt - issued_dt).total_seconds()
        if validity_seconds <= 0:
            raise BootstrapError("expires_at must be strictly greater than issued_at")
        if validity_seconds > 86400:  # 24 hours
            raise BootstrapError(
                f"Approval validity window exceeds 24 hours ({validity_seconds:.0f}s > 86400s)"
            )

        data = {
            "action": "bootstrap_initial_admins",
            "environment": environment,
            "expires_at": format_iso_utc(expires_dt),
            "instance_id": instance_id,
            "issued_at": format_iso_utc(issued_dt),
            "operator_id": operator_id,
            "request_id": request_id,
            "target_subs": [target_subs[0], target_subs[1]],
        }
    else:
        data = {
            "action": "bootstrap_initial_admins",
            "environment": environment,
            "target_subs": [target_subs[0], target_subs[1]],
        }

    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _load_ed25519_public_key(key_input: str | bytes) -> tuple[Ed25519PublicKey, str, bytes]:
    raw_bytes: bytes
    if isinstance(key_input, str):
        cleaned = key_input.strip()
        if "BEGIN PUBLIC KEY" in cleaned:
            pub_key = serialization.load_pem_public_key(cleaned.encode("utf-8"))
            if not isinstance(pub_key, Ed25519PublicKey):
                raise BootstrapError("Only Ed25519 public keys are supported")
            raw_bytes = pub_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
            fingerprint = hashlib.sha256(raw_bytes).hexdigest()
            return pub_key, fingerprint, raw_bytes
        else:
            try:
                raw_bytes = base64.b64decode(cleaned)
            except Exception as exc:
                raise BootstrapError("Invalid base64 encoding for public key") from exc
    else:
        raw_bytes = key_input

    if len(raw_bytes) != 32:
        raise BootstrapError("Ed25519 raw public key must be exactly 32 bytes")

    try:
        pub_key = Ed25519PublicKey.from_public_bytes(raw_bytes)
    except Exception as exc:
        raise BootstrapError(f"Failed to load Ed25519 public key: {exc}") from exc

    fingerprint = hashlib.sha256(raw_bytes).hexdigest()
    return pub_key, fingerprint, raw_bytes


def _decode_signature(sig_input: str | bytes) -> bytes:
    if isinstance(sig_input, str):
        cleaned = sig_input.strip()
        try:
            return base64.b64decode(cleaned)
        except Exception as exc:
            raise BootstrapError("Invalid base64 encoding for signature") from exc
    return sig_input


def bootstrap_initial_admins(
    db: DBSession,
    *,
    payload_data: dict[str, Any] | None = None,
    approvals: dict[str, str | bytes],
    now: datetime | None = None,
    _registry_backend: Any = None,
    **kwargs: Any,
) -> AdminBootstrapReceipt:
    """Execute one-time atomic System Admin bootstrap using fixed HKLM trust source.

    Validates:
    - Fixed HKLM 64-bit trust boundary reader
    - Exactly two distinct Ed25519 public keys from HKLM
    - Singleton database instance UUID match
    - Canonical payload structure, distinct target users, operator claim
    - Strict UTC time validity <= 24 hours with zero clock skew
    - Pre-existing zero-admin precondition
    - Replay denial (single bootstrap receipt lock)
    - Target users active and authenticated
    - Distinct dual signatures over exact canonical payload
    - Atomic UserRole and AdminBootstrapReceipt creation
    """
    if kwargs:
        unknown = ", ".join(sorted(kwargs.keys()))
        raise BootstrapError(f"Caller-selected parameters or trust material rejected: {unknown}")

    if payload_data is None or not isinstance(payload_data, dict):
        raise BootstrapError(
            "Caller-selected parameters or trust material rejected: "
            "missing or invalid payload_data; bootstrap requires canonical signed payload"
        )

    if now is None:
        now = datetime.now(timezone.utc)
    else:
        now = now.astimezone(timezone.utc)

    # 1. Validate payload structure (Hardened W9 flow)
    required_payload_fields = [
        "action",
        "environment",
        "target_subs",
        "instance_id",
        "request_id",
        "operator_id",
        "issued_at",
        "expires_at",
    ]
    for field in required_payload_fields:
        if field not in payload_data:
            raise BootstrapError(f"Missing required payload field '{field}'")

    if payload_data["action"] != "bootstrap_initial_admins":
        raise BootstrapError(
            f"Invalid payload action '{payload_data['action']}'; "
            "expected 'bootstrap_initial_admins'"
        )

    environment = payload_data["environment"]
    target_subs = payload_data["target_subs"]
    if not isinstance(target_subs, list) or len(target_subs) != 2:
        raise BootstrapError("Bootstrap requires exactly two target users")
    if target_subs[0] == target_subs[1]:
        raise BootstrapError("Bootstrap target users must be distinct")

    # 2. Validate instance binding against database singleton state
    instance_state = get_or_create_instance_state(db)
    if payload_data["instance_id"] != instance_state.instance_id:
        raise BootstrapError(
            f"Payload instance_id '{payload_data['instance_id']}' does not match "
            f"authoritative database instance '{instance_state.instance_id}'"
        )

    # 3. Validate UTC time boundaries with zero clock skew
    issued_dt = parse_iso_utc(payload_data["issued_at"])
    expires_dt = parse_iso_utc(payload_data["expires_at"])

    if issued_dt > now:
        raise BootstrapError(
            f"Approval issued_at ({payload_data['issued_at']}) is in the "
            "future relative to current time"
        )
    if now >= expires_dt:
        raise BootstrapError(
            f"Approval expired at {payload_data['expires_at']}; "
            f"current time is {format_iso_utc(now)}"
        )

    validity_seconds = (expires_dt - issued_dt).total_seconds()
    if validity_seconds <= 0 or validity_seconds > 86400:
        raise BootstrapError(
            f"Approval validity window must be >0 and <=24 hours; found {validity_seconds:.0f}s"
        )

    # 4. Check zero-admin precondition
    existing_admins = (
        db.query(UserRole)
        .filter(UserRole.role.in_([Role.SYSTEM_ADMIN.value, "System Admin"]))
        .count()
    )
    if existing_admins > 0:
        raise BootstrapError(
            "System Admin already exists; bootstrap is only permitted when zero System Admins exist"
        )

    # 5. Check single bootstrap receipt precondition (replay protection)
    existing_receipts = db.query(AdminBootstrapReceipt).count()
    if existing_receipts > 0:
        raise BootstrapError("Bootstrap has already been performed; replay rejected")

    # 6. Verify target users exist and are active
    u1 = db.query(User).filter_by(sub=target_subs[0]).first()
    if not u1:
        raise BootstrapError(
            f"User with sub '{target_subs[0]}' not found; users must first authenticate via OIDC"
        )
    if not u1.is_active:
        raise BootstrapError(f"Target user '{target_subs[0]}' is inactive or deprovisioned")

    u2 = db.query(User).filter_by(sub=target_subs[1]).first()
    if not u2:
        raise BootstrapError(
            f"User with sub '{target_subs[1]}' not found; users must first authenticate via OIDC"
        )
    if not u2.is_active:
        raise BootstrapError(f"Target user '{target_subs[1]}' is inactive or deprovisioned")

    if u1.id == u2.id:
        raise BootstrapError("Target user database IDs must be distinct")

    # 7. Read trusted public keys from fixed HKLM 64-bit trust boundary
    trusted_keys = load_trusted_approver_keys(_backend=_registry_backend)
    po_pub, po_fp, po_bytes = _load_ed25519_public_key(trusted_keys["project_owner"])
    sr_pub, sr_fp, sr_bytes = _load_ed25519_public_key(trusted_keys["security_reviewer"])

    if po_bytes == sr_bytes:
        raise BootstrapError(
            "Project Owner and Security Reviewer approver keys must be distinct; "
            "same-person approval rejected"
        )

    # 8. Verify dual signatures over exact canonical payload
    canonical_bytes = create_canonical_payload(
        payload_data["environment"],
        payload_data["target_subs"],
        instance_id=payload_data["instance_id"],
        request_id=payload_data["request_id"],
        operator_id=payload_data["operator_id"],
        issued_at=issued_dt,
        expires_at=expires_dt,
    )
    payload_digest = hashlib.sha256(canonical_bytes).hexdigest()

    if "project_owner" not in approvals:
        raise BootstrapError("Missing approval signature for 'project_owner'")
    if "security_reviewer" not in approvals:
        raise BootstrapError("Missing approval signature for 'security_reviewer'")

    po_sig = _decode_signature(approvals["project_owner"])
    sr_sig = _decode_signature(approvals["security_reviewer"])

    try:
        po_pub.verify(po_sig, canonical_bytes)
    except InvalidSignature:
        raise BootstrapError(
            "Invalid approval signature for Project Owner; payload or environment mismatch"
        ) from None
    except Exception as exc:
        raise BootstrapError(f"Project Owner signature verification failed: {exc}") from exc

    try:
        sr_pub.verify(sr_sig, canonical_bytes)
    except InvalidSignature:
        raise BootstrapError(
            "Invalid approval signature for Security Reviewer; payload or environment mismatch"
        ) from None
    except Exception as exc:
        raise BootstrapError(f"Security Reviewer signature verification failed: {exc}") from exc

    # 9. Atomic transaction: create receipt and user roles
    try:
        receipt = AdminBootstrapReceipt(
            environment=environment,
            target_user1_id=u1.id,
            target_user2_id=u2.id,
            target_sub1=target_subs[0],
            target_sub2=target_subs[1],
            approver1_role="project_owner",
            approver1_key_fingerprint=po_fp,
            approver2_role="security_reviewer",
            approver2_key_fingerprint=sr_fp,
            payload_digest=payload_digest,
            instance_id=payload_data["instance_id"],
            request_id=payload_data["request_id"],
            operator_id=payload_data["operator_id"],
            issued_at=issued_dt,
            expires_at=expires_dt,
            consumed=True,
            single_bootstrap_lock="BOOTSTRAP_LOCK",
        )
        db.add(receipt)
        db.flush()

        role1 = UserRole(
            user_id=u1.id,
            role=Role.SYSTEM_ADMIN.value,
            granted_by=None,
            second_admin_id=None,
            bootstrap_receipt_id=receipt.id,
        )
        role2 = UserRole(
            user_id=u2.id,
            role=Role.SYSTEM_ADMIN.value,
            granted_by=None,
            second_admin_id=None,
            bootstrap_receipt_id=receipt.id,
        )
        db.add(role1)
        db.add(role2)
        db.commit()
        db.refresh(receipt)
        return receipt
    except Exception as exc:
        db.rollback()
        raise BootstrapError(f"Atomic bootstrap transaction failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Stdin Ingestion and CLI Entrypoint
# ---------------------------------------------------------------------------
def run_bootstrap_from_stdin(
    db: DBSession,
    stdin_data: str | bytes,
    *,
    now: datetime | None = None,
    _registry_backend: Any = None,
) -> AdminBootstrapReceipt:
    """Ingest bounded JSON from stdin, parse dual signatures and payload, and execute bootstrap."""
    raw_bytes = stdin_data.encode("utf-8") if isinstance(stdin_data, str) else stdin_data
    if len(raw_bytes) > MAX_STDIN_BYTES:
        raise BootstrapError(
            f"Input exceeds maximum allowed size of {MAX_STDIN_BYTES} bytes "
            f"({len(raw_bytes)} bytes received)"
        )

    try:
        parsed_json = json.loads(raw_bytes.decode("utf-8"))
    except Exception as exc:
        raise BootstrapError("Invalid JSON input for bootstrap payload") from exc

    if not isinstance(parsed_json, dict):
        raise BootstrapError("Bootstrap input JSON must be an object")

    if "payload" not in parsed_json:
        raise BootstrapError("Missing 'payload' object in bootstrap input")
    if "signatures" not in parsed_json:
        raise BootstrapError("Missing 'signatures' object in bootstrap input")

    payload_data = parsed_json["payload"]
    signatures = parsed_json["signatures"]

    if not isinstance(payload_data, dict):
        raise BootstrapError("'payload' must be a JSON object")
    if not isinstance(signatures, dict):
        raise BootstrapError("'signatures' must be a JSON object")

    return bootstrap_initial_admins(
        db,
        payload_data=payload_data,
        approvals=signatures,
        now=now,
        _registry_backend=_registry_backend,
    )


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "One-time offline initial System Admin bootstrap command.\n"
            "Accepts bounded JSON approval and signatures from stdin."
        )
    )
    return parser.parse_args(args)


def main(args: list[str] | None = None) -> int:
    _ = parse_args(args)

    settings = Settings()
    engine = build_engine(settings)
    if engine is None:
        sys.stderr.write("Database engine not configured; set DATABASE_URL in environment\n")
        return 1

    try:
        stdin_content = sys.stdin.read(MAX_STDIN_BYTES + 1)
        if len(stdin_content.encode("utf-8")) > MAX_STDIN_BYTES:
            sys.stderr.write(
                f"BOOTSTRAP REJECTED: Input exceeds maximum allowed size of "
                f"{MAX_STDIN_BYTES} bytes\n"
            )
            return 1
    except Exception as exc:
        sys.stderr.write(f"BOOTSTRAP REJECTED: Failed to read stdin: {exc}\n")
        return 1

    with DBSession(engine) as db:
        try:
            receipt = run_bootstrap_from_stdin(db, stdin_content)
            sys.stdout.write(
                f"SUCCESS: System Admin bootstrap completed.\n"
                f"Receipt ID: {receipt.id}\n"
                f"Instance ID: {receipt.instance_id}\n"
                f"Request ID: {receipt.request_id}\n"
                f"Environment: {receipt.environment}\n"
                f"Operator ID: {receipt.operator_id}\n"
                f"Target Sub 1: {receipt.target_sub1}\n"
                f"Target Sub 2: {receipt.target_sub2}\n"
                f"PO Fingerprint: {receipt.approver1_key_fingerprint}\n"
                f"SR Fingerprint: {receipt.approver2_key_fingerprint}\n"
                f"Payload Digest: {receipt.payload_digest}\n"
            )
            return 0
        except BootstrapError as exc:
            sys.stderr.write(f"BOOTSTRAP REJECTED: {exc}\n")
            return 1
        except Exception as exc:
            sys.stderr.write(f"UNEXPECTED ERROR: {exc}\n")
            return 1


if __name__ == "__main__":
    sys.exit(main())
