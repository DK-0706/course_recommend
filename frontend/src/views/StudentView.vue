<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, type Course, type UserSession } from '../api'
import CourseCard from '../components/CourseCard.vue'

const router = useRouter()
const user = ref<UserSession>({ authenticated: true })
const allCourses = ref<Course[]>([])
const chosenIds = ref<number[]>([])
const recommendations = ref<Course[]>([])
const reasons = ref<Record<string, string>>({})
const messages = ref<{ role: 'user' | 'assistant'; content: string }[]>([])
const chatText = ref('')
const chatShownIds = ref<number[]>([])
const loading = ref(false)
const chatLoading = ref(false)
const recommendationSource = ref<'profile' | 'chat'>('profile')
const error = ref('')
const chosenCourses = computed(() => allCourses.value.filter(course => chosenIds.value.includes(course.id)))
// The catalog always reflects all unchosen courses; chat results update only the recommendation panel.
const availableCourses = computed(() => allCourses.value.filter(course => !chosenIds.value.includes(course.id)))

async function load() {
  loading.value = true
  error.value = ''
  try {
    user.value = await api<UserSession>('/api/auth/me')
    const result = await api<{ courses: Course[]; chosen_ids: number[] }>('/api/student/courses')
    allCourses.value = result.courses
    chosenIds.value = result.chosen_ids
    await loadRecommendations()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '课程加载失败'
  } finally {
    loading.value = false
  }
}

async function loadRecommendations() {
  recommendations.value = await api<Course[]>('/api/student/recommend')
  recommendationSource.value = 'profile'
  reasons.value = {}
  if (!recommendations.value.length) return
  try {
    reasons.value = await api<Record<string, string>>('/api/student/reason', {
      method: 'POST', body: JSON.stringify({ course_ids: recommendations.value.map(course => course.id) }),
    })
  } catch {
    // Cards remain useful if the optional explanation service is unavailable.
  }
}

async function choose(course: Course, type: 'add' | 'del') {
  const verb = type === 'add' ? '选课' : '退选'
  if (!window.confirm(`确认${verb}“${course.name}”吗？`)) return
  try {
    const result = await api<{ msg: string }>('/api/student/choose', {
      method: 'POST', body: JSON.stringify({ cid: course.id, type }),
    })
    if (result.msg !== '操作成功') throw new Error(result.msg)
    chosenIds.value = type === 'add'
      ? [...chosenIds.value, course.id]
      : chosenIds.value.filter(id => id !== course.id)
    await loadRecommendations()
  } catch (err) {
    window.alert(err instanceof Error ? err.message : '选课操作失败')
  }
}

async function sendChat() {
  const message = chatText.value.trim()
  if (!message || chatLoading.value) return
  chatText.value = ''
  messages.value.push({ role: 'user', content: message })
  chatLoading.value = true
  try {
    const result = await api<{ success: boolean; msg?: string; reply: string; courses: Course[] }>('/api/student/chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        history: messages.value.slice(0, -1),
        shown_ids: chatShownIds.value,
      }),
    })
    if (!result.success) throw new Error(result.msg || '推荐失败')
    messages.value.push({ role: 'assistant', content: result.reply })
    for (const course of result.courses || []) {
      if (!chatShownIds.value.includes(course.id)) chatShownIds.value.push(course.id)
    }
    const chatCourses = Array.isArray(result.courses) ? result.courses : []
    if (chatCourses.length) {
      recommendations.value = chatCourses
      recommendationSource.value = 'chat'
      reasons.value = Object.fromEntries(
        chatCourses
          .filter(course => course.reason)
          .map(course => [String(course.id), course.reason as string]),
      )
    }
  } catch (err) {
    messages.value.push({ role: 'assistant', content: err instanceof Error ? err.message : '请求失败，请稍后重试' })
  } finally {
    chatLoading.value = false
  }
}

async function logout() {
  await api('/api/auth/logout', { method: 'POST' })
  await router.push('/login/student')
}

onMounted(load)
</script>

<template>
  <main class="app-page">
    <header class="topbar">
      <RouterLink class="brand" to="/student"><span class="brand-mark brand-mark--small">C</span><span>Course Compass<small>课程推荐系统</small></span></RouterLink>
      <div class="topbar-user"><span class="avatar">{{ (user.name || '同').slice(0, 1) }}</span><span>欢迎，{{ user.name || '同学' }}</span><button class="button button--ghost" @click="logout">退出</button></div>
    </header>
    <section class="page-heading">
      <div><p class="eyebrow">STUDENT SPACE</p><h1>找到适合你的下一门课</h1><p class="muted">从你的学习记录和兴趣出发，探索更多可能。</p></div>
      <div class="heading-stat"><strong>{{ chosenIds.length }}</strong><span>已选课程</span></div>
    </section>
    <p v-if="error" class="banner banner--error">{{ error }}</p>

    <section class="panel">
      <div class="section-heading"><div><span class="section-icon section-icon--green">✓</span><div><h2>已选课程</h2><p>你的当前学习计划</p></div></div><span class="count-pill">{{ chosenCourses.length }} 门</span></div>
      <div v-if="chosenCourses.length" class="course-grid">
        <CourseCard v-for="course in chosenCourses" :key="course.id" :course="course" tone="green" action="退选" @action="choose(course, 'del')" />
      </div>
      <div v-else class="empty-state">还没有选课，先去下面的课程库看看吧。</div>
    </section>

    <section class="panel chat-panel">
      <div class="section-heading"><div><span class="section-icon section-icon--blue">✦</span><div><h2>对话选课</h2><p>描述你的兴趣、目标或偏好</p></div></div><span class="live-dot">AI 助手</span></div>
      <div class="chat-box">
        <div v-if="!messages.length" class="chat-hint">试试说：“我想学人工智能相关的课”或“再换一批”</div>
        <div v-for="(message, index) in messages" :key="index" class="chat-message" :class="`chat-message--${message.role}`">
          <span class="chat-avatar">{{ message.role === 'user' ? '我' : 'AI' }}</span><p>{{ message.content }}</p>
        </div>
        <div v-if="chatLoading" class="chat-message"><span class="chat-avatar">AI</span><p class="typing">正在整理课程建议…</p></div>
      </div>
      <form class="chat-input" @submit.prevent="sendChat"><input v-model="chatText" placeholder="例如：推荐几门适合入门的编程课" :disabled="chatLoading" /><button class="button button--primary" :disabled="chatLoading || !chatText.trim()">发送 <span>↗</span></button></form>
    </section>

    <section class="panel recommendation-panel">
      <div class="section-heading"><div><span class="section-icon section-icon--purple">✧</span><div><h2>为你推荐</h2><p>{{ recommendationSource === 'chat' ? '已根据刚才的对话更新课程建议' : '结合你的选课记录与课程内容' }}</p></div></div><button class="button button--outline" :disabled="loading" @click="loadRecommendations">↻ 换一批</button></div>
      <div v-if="loading" class="empty-state">正在载入推荐…</div>
      <div v-else-if="recommendations.length" class="course-grid">
        <CourseCard v-for="course in recommendations" :key="course.id" :course="course" tone="purple" :reason="reasons[String(course.id)] || ''" :action="chosenIds.includes(course.id) ? '已选' : '加入课程'" :disabled="chosenIds.includes(course.id)" @action="choose(course, 'add')" />
      </div>
      <div v-else class="empty-state">暂无推荐课程，试着先选几门课程。</div>
    </section>

    <section class="panel">
      <div class="section-heading"><div><span class="section-icon section-icon--slate">▦</span><div><h2>课程库</h2><p>浏览全部可选课程</p></div></div><span class="count-pill">{{ availableCourses.length }} 门可选</span></div>
      <div v-if="availableCourses.length" class="course-grid">
        <CourseCard v-for="course in availableCourses" :key="course.id" :course="course" action="加入课程" @action="choose(course, 'add')" />
      </div>
      <div v-else class="empty-state">课程正在载入…</div>
    </section>
    <footer class="footer-note">Course Compass · 为每一次学习选择提供方向</footer>
  </main>
</template>
