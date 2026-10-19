<script setup lang="ts">
import type { Course } from '../api'

withDefaults(defineProps<{
  course: Course
  tone?: 'purple' | 'green' | 'plain'
  action?: string
  reason?: string
  disabled?: boolean
}>(), { tone: 'plain', action: '', reason: '', disabled: false })

const emit = defineEmits<{ action: [] }>()

function trackPointer(event: PointerEvent) {
  const card = event.currentTarget as HTMLElement
  const bounds = card.getBoundingClientRect()
  card.style.setProperty('--pointer-x', `${event.clientX - bounds.left}px`)
  card.style.setProperty('--pointer-y', `${event.clientY - bounds.top}px`)
}
</script>

<template>
  <article class="course-card" :class="`tone-${tone}`" @pointermove="trackPointer">
    <div class="course-card__top">
      <span class="course-tag">{{ course.type || '课程' }}</span>
      <span class="credit">{{ course.credit }} 学分</span>
    </div>
    <h3>{{ course.name }}</h3>
    <p class="muted">{{ course.teacher || '教师待定' }}</p>
    <p v-if="course.intro" class="course-intro">{{ course.intro }}</p>
    <p v-if="reason" class="reason">✦ {{ reason }}</p>
    <button v-if="action" class="button button--small" :disabled="disabled" @click="emit('action')">
      {{ action }}
    </button>
  </article>
</template>
