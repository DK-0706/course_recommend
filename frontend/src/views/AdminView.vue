<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, type Course, type UserSession } from '../api'

interface Student { id: number; name: string; major: string; grade: string }
interface Teacher { id: number; name: string; title: string; department: string }

const route = useRoute()
const router = useRouter()
const user = ref<UserSession>({ authenticated: true })
const tab = ref<'students' | 'teachers' | 'courses'>('students')
const students = ref<Student[]>([])
const teachers = ref<Teacher[]>([])
const courses = ref<Course[]>([])
const logs = ref<string[]>([])
const error = ref('')
const studentForm = reactive({ name: '', major: '', grade: '', password: '' })
const teacherForm = reactive({ name: '', title: '', department: '', password: '' })
const courseForm = reactive({ id: '', name: '', teacher_id: '', credit: '', type: '', intro: '' })
const resetForm = reactive({ type: 'student', id: '', new_password: '' })

async function load() {
  user.value = await api<UserSession>('/api/auth/me')
  if (route.path === '/admin/logs') {
    const result = await api<{ logs: string[] }>('/api/admin/logs')
    logs.value = result.logs
    return
  }
  const [studentList, teacherList, courseList] = await Promise.all([
    api<Student[]>('/api/admin/students'), api<Teacher[]>('/api/admin/teachers'), api<Course[]>('/api/admin/courses'),
  ])
  students.value = studentList
  teachers.value = teacherList
  courses.value = courseList
}

async function addStudent() {
  try {
    await api('/api/admin/students', { method: 'POST', body: JSON.stringify(studentForm) })
    Object.assign(studentForm, { name: '', major: '', grade: '', password: '' })
    students.value = await api<Student[]>('/api/admin/students')
  } catch (err) { error.value = err instanceof Error ? err.message : '添加学生失败' }
}

async function addTeacher() {
  try {
    await api('/api/admin/teachers', { method: 'POST', body: JSON.stringify(teacherForm) })
    Object.assign(teacherForm, { name: '', title: '', department: '', password: '' })
    teachers.value = await api<Teacher[]>('/api/admin/teachers')
  } catch (err) { error.value = err instanceof Error ? err.message : '添加教师失败' }
}

async function addCourse() {
  try {
    await api('/api/admin/courses', { method: 'POST', body: JSON.stringify(courseForm) })
    Object.assign(courseForm, { id: '', name: '', teacher_id: '', credit: '', type: '', intro: '' })
    courses.value = await api<Course[]>('/api/admin/courses')
  } catch (err) { error.value = err instanceof Error ? err.message : '添加课程失败' }
}

async function remove(kind: 'students' | 'teachers' | 'courses', id: number, name: string) {
  if (!window.confirm(`确定删除${name}吗？`)) return
  try {
    await api(`/api/admin/${kind}/${id}`, { method: 'DELETE' })
    await load()
  } catch (err) { error.value = err instanceof Error ? err.message : '删除失败' }
}

async function resetPassword() {
  try {
    const result = await api<{ success: boolean; msg: string }>('/api/admin/password', {
      method: 'POST', body: JSON.stringify(resetForm),
    })
    if (!result.success) throw new Error(result.msg)
    window.alert('密码已重置')
    resetForm.id = ''
    resetForm.new_password = ''
  } catch (err) { error.value = err instanceof Error ? err.message : '重置密码失败' }
}

async function logout() {
  await api('/api/auth/logout', { method: 'POST' })
  await router.push('/login/admin')
}

onMounted(load)
watch(() => route.fullPath, load)
</script>

<template>
  <main class="app-page app-page--wide">
    <header class="topbar">
      <RouterLink class="brand" to="/admin"><span class="brand-mark brand-mark--small">C</span><span>Course Compass<small>系统管理</small></span></RouterLink>
      <div class="topbar-user"><span class="avatar avatar--purple">{{ (user.name || '管').slice(0, 1) }}</span><span>欢迎，{{ user.name || '管理员' }}</span><button class="button button--ghost" @click="logout">退出</button></div>
    </header>
    <section class="page-heading"><div><p class="eyebrow">ADMIN CONSOLE</p><h1>{{ route.path === '/admin/logs' ? '系统日志' : '管理控制台' }}</h1><p class="muted">管理学生、教师和课程数据。</p></div><RouterLink v-if="route.path === '/admin/logs'" class="button button--outline" to="/admin">返回管理台</RouterLink><RouterLink v-else class="button button--outline" to="/admin/logs">查看系统日志</RouterLink></section>
    <p v-if="error" class="banner banner--error">{{ error }}</p>

    <section v-if="route.path === '/admin/logs'" class="panel"><div class="section-heading"><div><span class="section-icon section-icon--slate">≡</span><div><h2>最近异常记录</h2><p>最近 50 行系统日志</p></div></div></div><pre class="log-view">{{ logs.join('') }}</pre></section>

    <template v-else>
      <section class="stats-grid">
        <button class="stat-card" :class="{ 'stat-card--active': tab === 'students' }" @click="tab = 'students'"><span class="stat-icon stat-icon--blue">♙</span><span><small>学生</small><strong>{{ students.length }}</strong></span></button>
        <button class="stat-card" :class="{ 'stat-card--active': tab === 'teachers' }" @click="tab = 'teachers'"><span class="stat-icon stat-icon--green">♧</span><span><small>教师</small><strong>{{ teachers.length }}</strong></span></button>
        <button class="stat-card" :class="{ 'stat-card--active': tab === 'courses' }" @click="tab = 'courses'"><span class="stat-icon stat-icon--purple">▤</span><span><small>课程</small><strong>{{ courses.length }}</strong></span></button>
      </section>

      <section v-if="tab === 'students'" class="panel">
        <div class="section-heading"><div><span class="section-icon section-icon--blue">♙</span><div><h2>学生管理</h2><p>添加和维护学生账号</p></div></div></div>
        <form class="inline-form" @submit.prevent="addStudent"><input v-model="studentForm.name" required placeholder="姓名" /><input v-model="studentForm.major" placeholder="专业" /><input v-model="studentForm.grade" placeholder="年级" /><input v-model="studentForm.password" type="password" placeholder="初始密码（默认 123456）" /><button class="button button--primary">添加学生</button></form>
        <div class="table-wrap"><table><thead><tr><th>ID</th><th>姓名</th><th>专业</th><th>年级</th><th>操作</th></tr></thead><tbody><tr v-for="student in students" :key="student.id"><td class="mono">{{ student.id }}</td><td class="strong">{{ student.name }}</td><td>{{ student.major || '—' }}</td><td>{{ student.grade || '—' }}</td><td><button class="text-button text-button--danger" @click="remove('students', student.id, student.name)">删除</button></td></tr><tr v-if="!students.length"><td colspan="5" class="table-empty">暂无学生</td></tr></tbody></table></div>
      </section>

      <section v-else-if="tab === 'teachers'" class="panel">
        <div class="section-heading"><div><span class="section-icon section-icon--green">♧</span><div><h2>教师管理</h2><p>添加和维护教师账号</p></div></div></div>
        <form class="inline-form" @submit.prevent="addTeacher"><input v-model="teacherForm.name" required placeholder="姓名" /><input v-model="teacherForm.title" placeholder="职称" /><input v-model="teacherForm.department" placeholder="院系" /><input v-model="teacherForm.password" type="password" placeholder="初始密码（默认 123456）" /><button class="button button--primary">添加教师</button></form>
        <div class="table-wrap"><table><thead><tr><th>ID</th><th>姓名</th><th>职称</th><th>院系</th><th>操作</th></tr></thead><tbody><tr v-for="teacher in teachers" :key="teacher.id"><td class="mono">{{ teacher.id }}</td><td class="strong">{{ teacher.name }}</td><td>{{ teacher.title || '—' }}</td><td>{{ teacher.department || '—' }}</td><td><button class="text-button text-button--danger" @click="remove('teachers', teacher.id, teacher.name)">删除</button></td></tr><tr v-if="!teachers.length"><td colspan="5" class="table-empty">暂无教师</td></tr></tbody></table></div>
      </section>

      <section v-else class="panel">
        <div class="section-heading"><div><span class="section-icon section-icon--purple">▤</span><div><h2>课程管理</h2><p>维护课程目录和授课教师</p></div></div></div>
        <form class="inline-form" @submit.prevent="addCourse"><input v-model="courseForm.id" required type="number" placeholder="课程号" /><input v-model="courseForm.name" required placeholder="课程名" /><select v-model="courseForm.teacher_id"><option value="">暂无教师</option><option v-for="teacher in teachers" :key="teacher.id" :value="String(teacher.id)">{{ teacher.name }} · {{ teacher.id }}</option></select><input v-model="courseForm.credit" required type="number" min="0" placeholder="学分" /><input v-model="courseForm.type" placeholder="课程类型" /><input v-model="courseForm.intro" placeholder="课程简介" /><button class="button button--primary">添加课程</button></form>
        <div class="table-wrap"><table><thead><tr><th>课号</th><th>课程名</th><th>教师</th><th>学分</th><th>类型</th><th>操作</th></tr></thead><tbody><tr v-for="course in courses" :key="course.id"><td class="mono">{{ course.id }}</td><td class="strong">{{ course.name }}</td><td>{{ course.teacher || '—' }}</td><td>{{ course.credit }}</td><td>{{ course.type || '—' }}</td><td><button class="text-button text-button--danger" @click="remove('courses', course.id, course.name)">删除</button></td></tr><tr v-if="!courses.length"><td colspan="6" class="table-empty">暂无课程</td></tr></tbody></table></div>
      </section>

      <section class="panel reset-panel"><div class="section-heading"><div><span class="section-icon section-icon--slate">⌑</span><div><h2>重置密码</h2><p>为学生或教师设置新密码</p></div></div></div><form class="inline-form" @submit.prevent="resetPassword"><select v-model="resetForm.type"><option value="student">学生</option><option value="teacher">教师</option></select><input v-model="resetForm.id" required type="number" placeholder="用户 ID" /><input v-model="resetForm.new_password" type="password" placeholder="新密码（默认 123456）" /><button class="button button--outline">重置密码</button></form></section>
    </template>
    <footer class="footer-note">Course Compass · 管理控制台</footer>
  </main>
</template>
