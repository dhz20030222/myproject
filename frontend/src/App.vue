<script setup>
import { ref } from 'vue'

const question = ref('') 
const chatHistory = ref([
  { role: 'ai', content: '你好！我是你的吉大考研复试助手，有什么想问的吗？' }
])
const isLoading = ref(false)

const sendMessage = async () => {
  if (!question.value.trim()) return

  // 1. 显示用户问题
  const userText = question.value
  chatHistory.value.push({ role: 'user', content: userText })
  question.value = ''
  isLoading.value = true

  try {
    // 2. 发送给 Python 后端
    const res = await fetch('http://127.0.0.1:8000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: userText })
    })
    
    const data = await res.json()
    
    // 3. 显示 AI 回答
    chatHistory.value.push({ role: 'ai', content: data.data })
  } catch (error) {
    chatHistory.value.push({ role: 'ai', content: '连接出错啦！请检查 main.py 是否运行。' })
    console.error(error)
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="chat-container">
    <div class="header">🎓 吉大考研智能助手</div>
    
    <div class="messages">
      <div v-for="(msg, i) in chatHistory" :key="i" 
           class="message-row" :class="msg.role === 'user' ? 'right' : 'left'">
        <div class="avatar">{{ msg.role === 'user' ? '🧑‍💻' : '🤖' }}</div>
        <div class="bubble">{{ msg.content }}</div>
      </div>
      <div v-if="isLoading" class="loading">思考中...</div>
    </div>

    <div class="input-box">
      <input v-model="question" @keyup.enter="sendMessage" placeholder="请输入问题..." />
      <button @click="sendMessage" :disabled="isLoading">发送</button>
    </div>
  </div>
</template>

<style scoped>
.chat-container { max-width: 600px; margin: 20px auto; border: 1px solid #ddd; border-radius: 10px; height: 80vh; display: flex; flex-direction: column; font-family: sans-serif; background-color: #f5f7fa; }
.header { background: #007bff; color: white; padding: 15px; text-align: center; font-weight: bold; border-radius: 10px 10px 0 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
.messages { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 15px; }
.message-row { display: flex; gap: 10px; align-items: flex-start; }
.right { flex-direction: row-reverse; }
.avatar { font-size: 24px; }
.bubble { padding: 10px 15px; border-radius: 10px; max-width: 70%; line-height: 1.5; white-space: pre-wrap; word-break: break-all; }
.left .bubble { background: white; border: 1px solid #eee; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
.right .bubble { background: #95ec69; color: black; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
.input-box { padding: 15px; background: white; border-top: 1px solid #ddd; display: flex; gap: 10px; border-radius: 0 0 10px 10px; }
input { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 5px; outline: none; font-size: 14px; }
input:focus { border-color: #007bff; }
button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; transition: background 0.2s; }
button:hover { background: #0056b3; }
button:disabled { background: #ccc; cursor: not-allowed; }
.loading { text-align: center; color: #999; font-size: 12px; margin-top: 5px; }
</style>