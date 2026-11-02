import { describe, expect, it } from 'vitest'
import { formatApiError } from './apiError'

describe('formatApiError', () => {
  const fallback = 'Lỗi mặc định'

  it('returns valid string details directly when non-empty', () => {
    expect(formatApiError('Lỗi xác thực', fallback)).toBe('Lỗi xác thực')
    expect(formatApiError('  Khoảng trắng  ', fallback)).toBe('Khoảng trắng')
  })

  it('returns fallback message for empty strings, null, undefined, and non-objects', () => {
    expect(formatApiError('', fallback)).toBe(fallback)
    expect(formatApiError('   ', fallback)).toBe(fallback)
    expect(formatApiError(null, fallback)).toBe(fallback)
    expect(formatApiError(undefined, fallback)).toBe(fallback)
    expect(formatApiError(12345, fallback)).toBe(fallback)
    expect(formatApiError(true, fallback)).toBe(fallback)
  })

  it('formats array of validation error objects without exposing input values', () => {
    const errorDetail = [
      {
        loc: ['body', 'title'],
        msg: 'Field required',
        type: 'value_error.missing',
        input: 'SECRET_UNTRUSTED_INPUT_1',
      },
      {
        loc: ['body', 'due_date'],
        msg: 'Invalid date format',
        type: 'type_error',
        input: 'SECRET_UNTRUSTED_INPUT_2',
      },
    ]

    const result = formatApiError(errorDetail, fallback)
    expect(result).toBe('title: Field required; due_date: Invalid date format')
    expect(result).not.toContain('SECRET_UNTRUSTED_INPUT_1')
    expect(result).not.toContain('SECRET_UNTRUSTED_INPUT_2')
  })

  it('formats single object-shaped detail safely', () => {
    const errorDetail = {
      loc: ['body', 'description'],
      msg: 'Too long',
      input: 'SECRET_INPUT_3',
    }

    const result = formatApiError(errorDetail, fallback)
    expect(result).toBe('description: Too long')
    expect(result).not.toContain('SECRET_INPUT_3')
  })

  it('supports message property as fallback for msg', () => {
    const errorDetail = {
      loc: ['name'],
      message: 'Name is required',
    }

    expect(formatApiError(errorDetail, fallback)).toBe('name: Name is required')
  })

  it('unwraps nested detail property if root error response object is passed', () => {
    const rootError = {
      detail: [
        {
          loc: ['body', 'project_name'],
          msg: 'Already exists',
        },
      ],
    }

    expect(formatApiError(rootError, fallback)).toBe('project_name: Already exists')
  })

  it('returns fallback message when error object or array has unknown/malformed shape', () => {
    expect(formatApiError([], fallback)).toBe(fallback)
    expect(formatApiError([{}], fallback)).toBe(fallback)
    expect(formatApiError([{ input: 'ONLY_INPUT' }], fallback)).toBe(fallback)
    expect(formatApiError({ input: 'ONLY_INPUT', random_field: 42 }, fallback)).toBe(fallback)
    expect(formatApiError({ foo: 'bar' }, fallback)).toBe(fallback)
  })
})
