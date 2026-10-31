import { Button } from '@/components/ui/button'
import { ProjectWorkbench } from '@/components/ProjectWorkbench'

export default function App() {
  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col justify-center gap-6 px-6 py-16">
      <p className="text-sm font-semibold tracking-widest text-slate-600">MÔI TRƯỜNG PHÁT TRIỂN</p>
      <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">CHÁNH HƯNG PMIS</h1>
      <p className="max-w-xl text-lg leading-relaxed text-slate-600">Nền tảng quản lý thông tin dự án đang được xây dựng.</p>
      <div><Button asChild><a href="/health/ready">Kiểm tra hệ thống</a></Button></div>
      <ProjectWorkbench />
    </main>
  )
}
