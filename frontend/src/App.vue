<script setup>
import { ref, onMounted, nextTick } from 'vue'
import axios from 'axios'

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
// 注意：Vue 跑在 5173，FastAPI 跑在 8000，必须写全路径
const API_BASE = "http://127.0.0.1:8000"

// --- 3. 生命周期: 页面加载时执行 ---
onMounted(() => {
  refreshFiles()
})

// --- 4. 核心功能函数 ---

// 获取文件列表
const refreshFiles = async () => {
  try {
    const res = await axios.get(`${API_BASE}/files`)
    fileList.value = res.data.files
  } catch (e) {
    console.error("获取列表失败", e)
  }
}

// 选中文件
const selectFile = (file) => {
  selectedFile.value = file
}

// 触发上传点击
const triggerUpload = () => {
  fileInput.value.click()
}

// 处理文件上传
const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  uploadStatus.value = "上传中..."
  const formData = new FormData()
  formData.append('file', file)

  try {
    const res = await axios.post(`${API_BASE}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    alert(res.data.message) // 弹出后端返回的成功消息
    uploadStatus.value = ""
    refreshFiles() // 刷新列表
  } catch (e) {
    alert("上传失败: " + (e.response?.data?.detail || str(e)))
    uploadStatus.value = "上传失败"
  }
}

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim()) return

  // 1. 用户消息上屏
  const text = inputMessage.value
  chatHistory.value.push({ role: 'user', content: text })
  inputMessage.value = ""
  isLoading.value = true
  scrollToBottom()

  // 2. 发送请求
  try {
    const res = await axios.post(`${API_BASE}/chat`, {
      text: text,
      filename: selectedFile.value // 告诉后端我在针对哪个文件提问
    })
    
    // 3. AI 消息上屏
    chatHistory.value.push({ role: 'ai', content: res.data.data })
  } catch (e) {
    chatHistory.value.push({ role: 'ai', content: "❌ 服务器连接失败" })
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (chatWindow.value) {
      chatWindow.value.scrollTop = chatWindow.value.scrollHeight
    }
  })
}

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
/* 样式重置 */
.app-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  font-family: 'Segoe UI', sans-serif;
  color: #333;
}

/* 左侧栏 */
.sidebar {
  width: 260px;
  background-color: #2c3e50;
  color: white;
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.upload-btn {
  width: 100%;
  padding: 10px;
  background: transparent;
  border: 1px dashed #aaa;
  color: white;
  cursor: pointer;
  border-radius: 4px;
  margin-top: 10px;
}
.upload-btn:hover { background: rgba(255,255,255,0.1); }

.list-header {
  margin-top: 20px;
  font-size: 0.85rem;
  color: #aaa;
  margin-bottom: 10px;
}

.file-item {
  padding: 10px;
  cursor: pointer;
  border-radius: 4px;
  margin-bottom: 4px;
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.file-item:hover { background: rgba(255,255,255,0.1); }
.file-item.active { background: #42b983; color: white; }

/* 右侧聊天 */
.main-chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f4f7f6;
}

.chat-header {
  padding: 15px 20px;
  background: white;
  border-bottom: 1px solid #ddd;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.mode-tag { font-weight: bold; color: #2c3e50; font-size: 0.9rem; }
.clear-btn { background: none; border: none; color: #999; cursor: pointer; }

.chat-window {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.empty-state {
  text-align: center;
  color: #aaa;
  margin-top: 100px;
}

.message-row { display: flex; gap: 10px; max-width: 80%; }
.message-row.user { align-self: flex-end; flex-direction: row-reverse; }
.message-row.ai { align-self: flex-start; }

.avatar { font-size: 1.5rem; }
.bubble {
  padding: 12px 16px;
  border-radius: 8px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
}
.user .bubble { background: #42b983; color: white; }
.ai .bubble { background: white; border: 1px solid #e0e0e0; }

.input-area {
  padding: 20px;
  background: white;
  display: flex;
  gap: 10px;
}
input {
  flex: 1;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  outline: none;
}
button {
  padding: 0 25px;
  background: #42b983;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
button:disabled { background: #ccc; }
</style>