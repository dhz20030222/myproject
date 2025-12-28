<script setup>
import { ref, onMounted, nextTick } from 'vue'
// 注意：我把 import axios 删掉了，以后不需要它了！

// --- 1. 变量定义 ---
const fileList = ref([])          // 文件列表
const selectedFile = ref(null)    // 当前选中的文件
const chatHistory = ref([])       // 聊天记录
const inputMessage = ref("")      // 输入框内容
const isLoading = ref(false)      // 加载状态
const fileInput = ref(null)       // 上传文件的 DOM 引用
const chatWindow = ref(null)      // 聊天窗口的 DOM 引用
const uploadStatus = ref("")      // 上传提示

// --- 2. 配置后端地址 ---
const API_BASE = "http://127.0.0.1:8000"

// --- 3. 生命周期 ---
onMounted(() => {
  refreshFiles()
})

// --- 4. 核心功能函数 ---

// A. 获取文件列表 (改用 fetch)
const refreshFiles = async () => {
  try {
    const res = await fetch(`${API_BASE}/files`)
    if (!res.ok) throw new Error("网络请求失败")
    
    const data = await res.json()
    fileList.value = data.files // 更新列表
    console.log("成功加载文件列表:", data.files)
  } catch (e) {
    console.error("获取列表失败:", e)
    // 可以在这里加个 alert 方便调试，发布时去掉
    // alert("无法连接到后端，请检查 python main.py 是否在运行")
  }
}

// B. 选中文件
const selectFile = (file) => {
  selectedFile.value = file
}

// C. 触发上传点击
const triggerUpload = () => {
  fileInput.value.click()
}

// D. 处理文件上传 (改用 fetch)
const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  uploadStatus.value = "上传中..."
  const formData = new FormData()
  formData.append('file', file)

  try {
    // fetch 上传不需要手动设置 Content-Type，它会自动识别
    const res = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      body: formData
    })
    
    const data = await res.json()
    
    if (res.ok) {
      alert("✅ " + data.message)
      uploadStatus.value = ""
      refreshFiles() // 上传成功后，立刻刷新列表
    } else {
      throw new Error(data.detail || "上传失败")
    }
  } catch (e) {
    alert("❌ 上传出错: " + e.message)
    uploadStatus.value = "上传失败"
  }
}

// E. 发送消息 (流式版 - 保持 fetch 不变)
const sendMessage = async () => {
  if (!inputMessage.value.trim()) return

  // 用户消息上屏
  const text = inputMessage.value
  chatHistory.value.push({ role: 'user', content: text })
  inputMessage.value = "" 
  
  // AI 消息占位
  const aiMessageIndex = chatHistory.value.push({ role: 'ai', content: "" }) - 1
  const aiMessage = chatHistory.value[aiMessageIndex]
  
  isLoading.value = true
  scrollToBottom()

  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: text,
        filename: selectedFile.value
      })
    })

    if (!response.ok) throw new Error("服务器连接失败")

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value, { stream: true })
      aiMessage.content += chunk
      scrollToBottom()
    }

  } catch (e) {
    console.error(e)
    aiMessage.content += "\n[❌ 哎呀，出错了]"
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

// 辅助函数：滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (chatWindow.value) {
      chatWindow.value.scrollTop = chatWindow.value.scrollHeight
    }
  })
}

// 辅助函数：清空
const clearHistory = () => {
  chatHistory.value = []
}
</script>

<template>
  <div class="app-container">
    <div class="sidebar">
      <h2>🤖 知识库助手</h2>
      
      <div class="upload-section">
        <input type="file" ref="fileInput" @change="handleFileUpload" style="display: none">
        <button class="upload-btn" @click="triggerUpload">
          + 上传 PDF
        </button>
        <div v-if="uploadStatus" class="status-text">{{ uploadStatus }}</div>
      </div>

      <div class="list-header">📚 现有资料 ({{ fileList.length }})</div>
      <div class="file-list">
        <div 
          class="file-item" 
          :class="{ active: selectedFile === null }"
          @click="selectFile(null)"
        >
          🌏 全部范围 (默认)
        </div>

        <div 
          v-for="file in fileList" 
          :key="file" 
          class="file-item"
          :class="{ active: selectedFile === file }"
          @click="selectFile(file)"
        >
          📄 {{ file }}
        </div>
      </div>
    </div>

    <div class="main-chat">
      <div class="chat-header">
        <span class="mode-tag">
          {{ selectedFile ? '当前模式: 限定搜索《' + selectedFile + '》' : '当前模式: 全库搜索' }}
        </span>
        <button class="clear-btn" @click="clearHistory">清空对话</button>
      </div>

      <div class="chat-window" ref="chatWindow">
        <div v-if="chatHistory.length === 0" class="empty-state">
          <h3>👋 你好！我是你的 AI 学习助手</h3>
          <p>请上传考研资料，或者直接向我提问。</p>
        </div>

        <div v-for="(msg, index) in chatHistory" :key="index" class="message-row" :class="msg.role">
          <div class="avatar">{{ msg.role === 'user' ? '🧑‍🎓' : '🤖' }}</div>
          <div class="bubble">{{ msg.content }}</div>
        </div>
        
        <div v-if="isLoading" class="message-row ai">
          <div class="avatar">🤖</div>
          <div class="bubble loading">正在思考中...</div>
        </div>
      </div>

      <div class="input-area">
        <input 
          type="text" 
          v-model="inputMessage" 
          @keyup.enter="sendMessage"
          placeholder="请输入你的问题..." 
          :disabled="isLoading"
        >
        <button @click="sendMessage" :disabled="isLoading || !inputMessage.trim()">发送</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 保持样式不变，可以直接复用之前的 */
.app-container { display: flex; height: 100vh; width: 100vw; font-family: 'Segoe UI', sans-serif; color: #333; }
.sidebar { width: 260px; background-color: #2c3e50; color: white; display: flex; flex-direction: column; padding: 20px; }
.upload-btn { width: 100%; padding: 10px; background: transparent; border: 1px dashed #aaa; color: white; cursor: pointer; border-radius: 4px; margin-top: 10px; }
.upload-btn:hover { background: rgba(255,255,255,0.1); }
.list-header { margin-top: 20px; font-size: 0.85rem; color: #aaa; margin-bottom: 10px; }
.file-item { padding: 10px; cursor: pointer; border-radius: 4px; margin-bottom: 4px; font-size: 0.9rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.file-item:hover { background: rgba(255,255,255,0.1); }
.file-item.active { background: #42b983; color: white; }
.main-chat { flex: 1; display: flex; flex-direction: column; background: #f4f7f6; }
.chat-header { padding: 15px 20px; background: white; border-bottom: 1px solid #ddd; display: flex; justify-content: space-between; align-items: center; }
.mode-tag { font-weight: bold; color: #2c3e50; font-size: 0.9rem; }
.clear-btn { background: none; border: none; color: #999; cursor: pointer; }
.chat-window { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 15px; }
.empty-state { text-align: center; color: #aaa; margin-top: 100px; }
.message-row { display: flex; gap: 10px; max-width: 80%; }
.message-row.user { align-self: flex-end; flex-direction: row-reverse; }
.message-row.ai { align-self: flex-start; }
.avatar { font-size: 1.5rem; }
.bubble { padding: 12px 16px; border-radius: 8px; line-height: 1.5; white-space: pre-wrap; word-break: break-all; }
.user .bubble { background: #42b983; color: white; }
.ai .bubble { background: white; border: 1px solid #e0e0e0; }
.input-area { padding: 20px; background: white; display: flex; gap: 10px; }
input { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 6px; outline: none; }
button { padding: 0 25px; background: #42b983; color: white; border: none; border-radius: 6px; cursor: pointer; }
button:disabled { background: #ccc; }
</style>