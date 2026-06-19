let posts = []
let hasApiKeys = false
let currentFilter = 'all'
let isThreadMode = false
let selectedImagePath = null

// ---------- DOM ----------
const form          = document.getElementById('post-form')
const tweetBoxes    = document.getElementById('tweet-boxes')
const btnAddTweet   = document.getElementById('btn-add-tweet')
const btnPickImage  = document.getElementById('btn-pick-image')
const imagePreview  = document.getElementById('image-preview')
const previewImg    = document.getElementById('preview-img')
const btnRemoveImg  = document.getElementById('btn-remove-img')
const scheduleInput = document.getElementById('scheduled-at')
const postList      = document.getElementById('post-list')
const keyDot        = document.getElementById('key-dot')
const modeSingle    = document.getElementById('mode-single')
const modeThread    = document.getElementById('mode-thread')

// ---------- ツイートボックス生成 ----------

function createTweetBox(index) {
  const div = document.createElement('div')
  div.className = 'tweet-box'
  div.dataset.index = index

  const header = document.createElement('div')
  header.className = 'tweet-box-header'
  const label = document.createElement('span')
  label.textContent = isThreadMode ? `Tweet ${index + 1}` : ''

  const right = document.createElement('div')
  right.style.display = 'flex'
  right.style.alignItems = 'center'
  right.style.gap = '8px'

  const counter = document.createElement('span')
  counter.className = 'char-count'
  counter.textContent = '0/140'

  right.appendChild(counter)

  if (isThreadMode && index > 0) {
    const removeBtn = document.createElement('button')
    removeBtn.type = 'button'
    removeBtn.className = 'btn-remove-tweet'
    removeBtn.textContent = '✕'
    removeBtn.onclick = () => { div.remove(); reindexTweetBoxes() }
    right.appendChild(removeBtn)
  }

  header.appendChild(label)
  header.appendChild(right)

  const ta = document.createElement('textarea')
  ta.placeholder = index === 0 ? 'Write your post... (max 140 chars)' : 'Continue thread... (max 140 chars)'
  ta.maxLength = 140
  ta.addEventListener('input', () => {
    const len = ta.value.length
    counter.textContent = `${len}/140`
    counter.style.color = len > 140 ? '#ef4444' : len > 120 ? '#f59e0b' : '#64748b'
  })

  div.appendChild(header)
  div.appendChild(ta)
  return div
}

function reindexTweetBoxes() {
  const boxes = tweetBoxes.querySelectorAll('.tweet-box')
  boxes.forEach((box, i) => {
    box.dataset.index = i
    const label = box.querySelector('.tweet-box-header span')
    if (label) label.textContent = isThreadMode ? `Tweet ${i + 1}` : ''
  })
}

function initTweetBoxes() {
  tweetBoxes.innerHTML = ''
  tweetBoxes.appendChild(createTweetBox(0))
}

// ---------- モード切替 ----------

modeSingle.addEventListener('click', () => {
  isThreadMode = false
  modeSingle.classList.add('active')
  modeThread.classList.remove('active')
  btnAddTweet.style.display = 'none'
  initTweetBoxes()
})

modeThread.addEventListener('click', () => {
  isThreadMode = true
  modeThread.classList.add('active')
  modeSingle.classList.remove('active')
  btnAddTweet.style.display = 'block'
  initTweetBoxes()
})

btnAddTweet.addEventListener('click', () => {
  const boxes = tweetBoxes.querySelectorAll('.tweet-box')
  tweetBoxes.appendChild(createTweetBox(boxes.length))
})

// ---------- 画像選択 ----------

btnPickImage.addEventListener('click', async () => {
  const filePath = await window.api.pickImage()
  if (!filePath) return
  selectedImagePath = filePath
  previewImg.src = `file://${filePath}`
  imagePreview.style.display = 'block'
  btnPickImage.style.display = 'none'
})

btnRemoveImg.addEventListener('click', () => {
  selectedImagePath = null
  previewImg.src = ''
  imagePreview.style.display = 'none'
  btnPickImage.style.display = 'flex'
})

// ---------- 投稿追加 ----------

form.addEventListener('submit', async (e) => {
  e.preventDefault()
  const textareas = tweetBoxes.querySelectorAll('textarea')
  const tweets = Array.from(textareas).map(t => t.value.trim()).filter(Boolean)

  if (!tweets.length) return
  if (tweets.some(t => t.length > 140)) { alert('Each tweet must be 140 characters or less'); return }

  const scheduledAt = scheduleInput.value ? new Date(scheduleInput.value).toISOString() : null

  const post = isThreadMode && tweets.length > 1
    ? { type: 'thread', tweets, imagePath: selectedImagePath, scheduledAt }
    : { type: 'single', content: tweets[0], imagePath: selectedImagePath, scheduledAt }

  const newPost = await window.api.addPost(post)
  posts.unshift(newPost)
  renderPosts()

  initTweetBoxes()
  scheduleInput.value = ''
  selectedImagePath = null
  previewImg.src = ''
  imagePreview.style.display = 'none'
  btnPickImage.style.display = 'flex'
})

// ---------- フィルター ----------

document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'))
    btn.classList.add('active')
    currentFilter = btn.dataset.filter
    renderPosts()
  })
})

// ---------- レンダリング ----------

const STATUS = {
  draft:     { text: 'Draft',     cls: 'draft'     },
  scheduled: { text: 'Scheduled', cls: 'scheduled' },
  ready:     { text: 'Ready',     cls: 'ready'     },
  posted:    { text: 'Posted',    cls: 'posted'    },
}

function fmt(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function esc(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br>')
}

function renderPosts() {
  const list = currentFilter === 'all' ? posts : posts.filter(p => p.status === currentFilter)
  if (!list.length) { postList.innerHTML = '<p class="empty">No posts yet</p>'; return }

  postList.innerHTML = list.map(post => {
    const { text, cls } = STATUS[post.status] ?? { text: post.status, cls: '' }
    const actionable = ['draft','scheduled','ready'].includes(post.status)
    const isThread = post.type === 'thread'

    const contentHtml = isThread
      ? `<div class="post-type-badge">🧵 Thread (${post.tweets.length} tweets)</div>
         <div class="thread-tweets">${post.tweets.map((t, i) => `<div class="thread-tweet"><span style="color:#64748b;font-size:11px">${i+1}. </span>${esc(t)}</div>`).join('')}</div>`
      : `<div class="post-content">${esc(post.content)}</div>`

    const imageHtml = post.imagePath
      ? `<div class="post-image"><img src="file://${post.imagePath}" alt="attached image" /></div>`
      : ''

    const tweetLink = post.tweetIds?.length
      ? `<a class="tweet-link" href="https://x.com/i/web/status/${post.tweetIds[0]}" target="_blank">View on X →</a>`
      : ''

    const xBtn = actionable
      ? `<button class="btn-x" onclick="sendToX('${post.id}')" ${hasApiKeys ? '' : 'disabled'} title="${hasApiKeys ? 'Post to X' : 'API keys required'}">𝕏 Post</button>`
      : ''
    const manualBtn = actionable
      ? `<button class="btn-manual" onclick="markPosted('${post.id}')">✓ Mark as posted</button>`
      : ''

    return `
    <div class="post-card ${post.status === 'ready' ? 'ready-card' : ''}" data-id="${post.id}">
      ${contentHtml}
      ${imageHtml}
      <div class="post-meta">
        <span class="status-badge ${cls}">${text}</span>
        <span class="post-date">${post.scheduledAt ? '📅 ' + fmt(post.scheduledAt) : 'No date set'}</span>
        ${tweetLink}
      </div>
      <div class="post-actions">
        ${xBtn}${manualBtn}
        <button class="btn-delete" onclick="deletePost('${post.id}')">Delete</button>
      </div>
    </div>`
  }).join('')
}

// ---------- アクション ----------

window.sendToX = async (id) => {
  const post = posts.find(p => p.id === id)
  if (!post) return
  const preview = post.type === 'thread'
    ? `Post thread (${post.tweets.length} tweets)?\n\n${post.tweets[0].slice(0,40)}...`
    : `Post to X?\n\n${post.content}`
  if (!confirm(preview)) return

  const btn = document.querySelector(`[data-id="${id}"] .btn-x`)
  if (btn) { btn.disabled = true; btn.textContent = 'Posting...' }

  try {
    const updated = await window.api.postToX(id)
    const idx = posts.findIndex(p => p.id === id)
    if (idx !== -1) posts[idx] = updated
    renderPosts()
  } catch (err) {
    alert(`Post failed:\n${err.message}`)
    if (btn) { btn.disabled = false; btn.textContent = '𝕏 Post' }
  }
}

window.markPosted = async (id) => {
  const updated = await window.api.updateStatus(id, 'posted')
  const idx = posts.findIndex(p => p.id === id)
  if (idx !== -1) posts[idx] = updated
  renderPosts()
}

window.deletePost = async (id) => {
  if (!confirm('Delete this post?')) return
  await window.api.deletePost(id)
  posts = posts.filter(p => p.id !== id)
  renderPosts()
}

// ---------- 設定モーダル ----------

const modal     = document.getElementById('settings-modal')
const openBtn   = document.getElementById('open-settings')
const closeBtn  = document.getElementById('close-settings')
const saveBtn   = document.getElementById('save-settings')

openBtn.addEventListener('click', () => modal.classList.add('open'))
closeBtn.addEventListener('click', () => modal.classList.remove('open'))
modal.addEventListener('click', e => { if (e.target === modal) modal.classList.remove('open') })

saveBtn.addEventListener('click', async () => {
  const settings = {
    apiKey:       document.getElementById('s-api-key').value.trim(),
    apiSecret:    document.getElementById('s-api-secret').value.trim(),
    accessToken:  document.getElementById('s-access-token').value.trim(),
    accessSecret: document.getElementById('s-access-secret').value.trim(),
  }
  if (Object.values(settings).some(v => !v)) { alert('Please fill in all 4 keys'); return }
  await window.api.saveSettings(settings)
  hasApiKeys = true
  keyDot.classList.add('ok')
  modal.classList.remove('open')
  document.querySelectorAll('#settings-modal input').forEach(el => el.value = '')
})

// ---------- 初期化 ----------

async function init() {
  const [fetchedPosts, settings] = await Promise.all([
    window.api.getPosts(),
    window.api.getSettings(),
  ])
  posts = fetchedPosts
  hasApiKeys = settings.hasKeys
  if (hasApiKeys) keyDot.classList.add('ok')

  initTweetBoxes()
  renderPosts()

  // 自動投稿後にメインプロセスから通知を受け取って再描画
  window.api.onPostsUpdated(async () => {
    posts = await window.api.getPosts()
    renderPosts()
  })

  // 30秒ごとに予約状態をチェック
  setInterval(async () => {
    posts = await window.api.getPosts()
    renderPosts()
  }, 30000)
}

init()
