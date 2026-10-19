<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, type Course, type UserSession } from '../api'

const route = useRoute()
const router = useRouter()
const user = ref<UserSession>({ authenticated: true })
const courses = ref<Course[]>([])
const students = ref<{ id: number; name: string; major: string; grade: string }[]>([])
const selectedCourse = ref<Course | null>(null)
const busy = ref(false)
const error = ref('')
const action = computed(() => String(route.params.action || 'list'))
const courseId = computed(() => Number(route.params.id || 0))
const form = reactive({ id: '', name: '', credit: '', type: '', intro: '' })

async function load() {
  error.value = ''
  user.value = await api<UserSession>('/api/auth/me')
  if (action.value === 'edit') {
    selectedCourse.value = await api<Course>(`/api/teacher/courses/${courseId.value}`)
    Object.assign(form, {
      id: String(selectedCourse.value.id), name: selectedCourse.value.name,
      credit: String(selectedCourse.value.credit), type: selectedCourse.value.type || '',
      intro: selectedCourse.value.intro || '',
    })
  } else if (action.value === 'students') {
    const result = await api<{ course: Course; students: typeof students.value }>(`/api/teacher/courses/${courseId.value}/students`)
    selectedCourse.value = result.course
    students.value = result.students
  } else if (action.value === 'list') {
    courses.value = await api<Course[]>('/api/teacher/courses')
  }
}

async function submit() {
  busy.value = true
  error.value = ''
  try {
    const isEdit = action.value === 'edit'
    await api(isEdit ? `/api/teacher/courses/${courseId.value}` : '/api/teacher/courses', {
      method: isEdit ? 'PUT' : 'POST', body: JSON.stringify(form),
    })
    await router.push('/teacher')
  } catch (err) {
    error.value = err instanceof Error ? err.message : '保存失败'
  } finally {
    busy.value = false
  }
}

async function logout() {
  await api('/api/auth/logout', { method: 'POST' })
  await router.push('/login/teacher')
}

watch(() => route.fullPath, () => load())
onMounted(load)
</script>

<template>
  <main class="app-page">
    <header class="topbar">
      <RouterLink class="brand" to="/teacher"><span class="brand-mark brand-mark--small">C</span><span>Course Compass<small>教师工作台</small></span></RouterLink>
      <div class="topbar-user"><span class="avatar avatar--blue">{{ (user.name || '师').slice(0, 1) }}</span><span>欢迎，{{ user.name || '老师' }}</span><button class="button button--ghost" @click="logout">退出</button></div>
    </header>

    <section class="page-heading">
      <div><p class="eyebrow">TEACHER SPACE</p><h1>{{ action === 'list' ? '课程工作台' : action === 'add' ? '发布新课程' : action === 'edit' ? '编辑课程' : '选课学生' }}</h1><p class="muted">管理课程信息，了解学生的学习选择。</p></div>
      <button v-if="action === 'list'" class="button button--primary" @click="router.push('/teacher/course/add')">＋ 发布课程</button>
      <button v-else class="button button--outline" @click="router.push('/teacher')">返回课程列表</button>
    </section>
    <p v-if="error" class="banner banner--error">{{ error }}</p>

    <section v-if="action === 'list'" class="panel">
      <div class="section-heading"><div><span class="section-icon section-icon--blue">▤</span><div><h2>我的课程</h2><p>你发布的课程和选课情况</p></div></div><span class="count-pill">{{ courses.length }} 门</span></div>
      <div class="table-wrap"><table><thead><tr><th>课程号</th><th>课程名称</th><th>学分</th><th>课程类型</th><th>操作</th></tr></thead><tbody>
        <tr v-for="course in courses" :key="course.id"><td class="mono">{{ course.id }}</td><td class="strong">{{ course.name }}</td><td>{{ course.credit }}</td><td><span class="course-tag">{{ course.type || '未分类' }}</span></td><td class="actions"><button class="text-button" @click="router.push(`/teacher/course/edit/${course.id}`)">编辑</button><button class="text-button" @click="router.push(`/teacher/course/students/${course.id}`)">学生名单</button></td></tr>
        <tr v-if="!courses.length"><td colspan="5" class="table-empty">还没有发布课程</td></tr>
      </tbody></table></div>
    </section>

    <section v-else-if="action === 'add' || action === 'edit'" class="panel form-panel">
      <div class="section-heading"><div><span class="section-icon section-icon--purple">✎</span><div><h2>{{ action === 'edit' ? '课程信息' : '课程详情' }}</h2><p>填写课程的基本信息</p></div></div></div>
      <form class="form-grid" @submit.prevent="submit">
        <label v-if="action === 'add'">课程号<input v-model="form.id" type="number" required placeholder="例如 124" /></label>
        <label v-else>课程号<input :value="form.id" disabled /></label>
        <label>课程名称<input v-model="form.name" required placeholder="课程名称" /></label>
        <label>学分<input v-model="form.credit" type="number" min="0" required placeholder="学分" /></label>
        <label>课程类型<input v-model="form.type" placeholder="例如：专业选修" /></label>
        <label class="field-wide">课程简介<textarea v-model="form.intro" rows="4" placeholder="介绍课程内容和学习目标" /></label>
        <div class="field-wide form-actions"><button class="button button--primary" :disabled="busy">{{ busy ? '保存中…' : action === 'edit' ? '保存修改' : '发布课程' }}</button><button type="button" class="button button--outline" @click="router.push('/teacher')">取消</button></div>
      </form>
    </section>

    <section v-else class="panel">
      <div class="section-heading"><div><span class="section-icon section-icon--green">◎</span><div><h2>{{ selectedCourse?.name || '课程选课名单' }}</h2><p>课程号 {{ selectedCourse?.id }} · {{ students.length }} 位学生</p></div></div></div>
      <div class="table-wrap"><table><thead><tr><th>ID</th><th>学生姓名</th><th>专业</th><th>年级</th></tr></thead><tbody>
        <tr v-for="student in students" :key="student.id"><td class="mono">{{ student.id }}</td><td class="strong">{{ student.name }}</td><td>{{ student.major || '—' }}</td><td>{{ student.grade || '—' }}</td></tr>
        <tr v-if="!students.length"><td colspan="4" class="table-empty">还没有学生选修这门课程</td></tr>
      </tbody></table></div>
    </section>
    <footer class="footer-note">Course Compass · 教师课程管理</footer>
  </main>
</template>
