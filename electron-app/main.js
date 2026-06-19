const { app, BrowserWindow, ipcMain, Notification, dialog, safeStorage } = require('electron')
const path = require('path')
const fs = require('fs')
const { TwitterApi } = require('twitter-api-v2')

const DATA_FILE     = path.join(app.getPath('userData'), 'posts.json')
const SETTINGS_FILE = path.join(app.getPath('userData'), 'settings.enc')

// ---------- データ ----------

function loadPosts() {
  if (!fs.existsSync(DATA_FILE)) return []
  try { return JSON.parse(fs.readFileSync(DATA_FILE, 'utf-8')) } catch { return [] }
}

function savePosts(posts) {
  fs.writeFileSync(DATA_FILE, JSON.stringify(posts, null, 2))
}

// ---------- 設定（APIキー暗号化保存） ----------

function saveSettings(settings) {
  const json = JSON.stringify(settings)
  if (safeStorage.isEncryptionAvailable()) {
    fs.writeFileSync(SETTINGS_FILE, safeStorage.encryptString(json))
  } else {
    fs.writeFileSync(SETTINGS_FILE + '.plain', json)
  }
}

function loadSettings() {
  try {
    if (safeStorage.isEncryptionAvailable() && fs.existsSync(SETTINGS_FILE)) {
      return JSON.parse(safeStorage.decryptString(fs.readFileSync(SETTINGS_FILE)))
    }
    const p = SETTINGS_FILE + '.plain'
    if (fs.existsSync(p)) return JSON.parse(fs.readFileSync(p, 'utf-8'))
  } catch {}
  return {}
}

function getClient() {
  const s = loadSettings()
  if (!s.apiKey || !s.apiSecret || !s.accessToken || !s.accessSecret) {
    throw new Error('APIキーが設定されていません。設定画面から入力してください。')
  }
  return new TwitterApi({
    appKey: s.apiKey, appSecret: s.apiSecret,
    accessToken: s.accessToken, accessSecret: s.accessSecret,
  })
}

// ---------- X 投稿（単体・画像付き） ----------

async function postSingle(content, imagePath = null) {
  const client = getClient()
  if (imagePath && fs.existsSync(imagePath)) {
    const mediaId = await client.v1.uploadMedia(imagePath)
    const { data } = await client.v2.tweet({ text: content, media: { media_ids: [mediaId] } })
    return [data.id]
  }
  const { data } = await client.v2.tweet(content)
  return [data.id]
}

// ---------- X 投稿（スレッド） ----------

async function postThread(tweets, imagePath = null) {
  const client = getClient()
  const ids = []
  for (let i = 0; i < tweets.length; i++) {
    const opts = { text: tweets[i] }
    if (i === 0 && imagePath && fs.existsSync(imagePath)) {
      const mediaId = await client.v1.uploadMedia(imagePath)
      opts.media = { media_ids: [mediaId] }
    }
    if (i > 0) opts.reply = { in_reply_to_tweet_id: ids[i - 1] }
    const { data } = await client.v2.tweet(opts)
    ids.push(data.id)
  }
  return ids
}

async function postContent(post) {
  if (post.type === 'thread') {
    return postThread(post.tweets, post.imagePath)
  }
  return postSingle(post.content, post.imagePath)
}

// ---------- ウィンドウ ----------

let mainWin = null

function createWindow() {
  mainWin = new BrowserWindow({
    width: 960, height: 700, minWidth: 700, minHeight: 500,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true, nodeIntegration: false,
    },
    backgroundColor: '#0f172a',
  })
  mainWin.loadFile('index.html')
}

// ---------- 自動投稿スケジューラー ----------

function startScheduler() {
  setInterval(async () => {
    const posts = loadPosts()
    const now = new Date()
    let changed = false
    const s = loadSettings()
    const hasKeys = !!(s.apiKey && s.apiSecret && s.accessToken && s.accessSecret)

    for (const post of posts) {
      if (post.status !== 'scheduled' || new Date(post.scheduledAt) > now) continue

      if (hasKeys) {
        try {
          const tweetIds = await postContent(post)
          post.status  = 'posted'
          post.tweetIds = tweetIds
          post.postedAt = new Date().toISOString()
          new Notification({ title: 'Post published', body: post.content?.slice(0, 40) ?? 'Thread posted successfully' }).show()
        } catch (err) {
          post.status = 'ready'
          new Notification({ title: 'Auto-post failed', body: err.message }).show()
        }
      } else {
        post.status = 'ready'
        new Notification({ title: 'Post time reached', body: 'API keys not configured — please post manually' }).show()
      }
      changed = true
    }

    if (changed) {
      savePosts(posts)
      mainWin?.webContents.send('posts-updated')
    }
  }, 60 * 1000)
}

// ---------- IPC ----------

ipcMain.handle('get-posts', () => loadPosts())

ipcMain.handle('get-settings', () => {
  const s = loadSettings()
  return { hasKeys: !!(s.apiKey && s.apiSecret && s.accessToken && s.accessSecret) }
})

ipcMain.handle('save-settings', (_, settings) => { saveSettings(settings); return true })

ipcMain.handle('add-post', (_, post) => {
  const posts = loadPosts()
  const newPost = {
    id: Date.now().toString(),
    type: post.type ?? 'single',
    content: post.content ?? null,
    tweets: post.tweets ?? null,
    imagePath: post.imagePath ?? null,
    scheduledAt: post.scheduledAt ?? null,
    status: post.scheduledAt ? 'scheduled' : 'draft',
    tweetIds: [],
    createdAt: new Date().toISOString(),
  }
  posts.unshift(newPost)
  savePosts(posts)
  return newPost
})

ipcMain.handle('delete-post', (_, id) => { savePosts(loadPosts().filter(p => p.id !== id)); return true })

ipcMain.handle('update-status', (_, { id, status }) => {
  const posts = loadPosts()
  const post = posts.find(p => p.id === id)
  if (post) {
    post.status = status
    if (status === 'posted') post.postedAt = new Date().toISOString()
    savePosts(posts)
  }
  return post
})

ipcMain.handle('post-to-x', async (_, { id }) => {
  const posts = loadPosts()
  const post = posts.find(p => p.id === id)
  if (!post) throw new Error('投稿が見つかりません')
  const tweetIds = await postContent(post)
  post.status  = 'posted'
  post.tweetIds = tweetIds
  post.postedAt = new Date().toISOString()
  savePosts(posts)
  return post
})

// 画像ファイル選択ダイアログ
ipcMain.handle('pick-image', async () => {
  const result = await dialog.showOpenDialog(mainWin, {
    properties: ['openFile'],
    filters: [{ name: '画像', extensions: ['jpg', 'jpeg', 'png', 'gif', 'webp'] }],
  })
  return result.canceled ? null : result.filePaths[0]
})

// ---------- 起動 ----------

app.whenReady().then(() => {
  createWindow()
  startScheduler()
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
