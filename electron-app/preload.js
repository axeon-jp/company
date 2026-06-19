const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('api', {
  getPosts:       ()             => ipcRenderer.invoke('get-posts'),
  addPost:        (post)         => ipcRenderer.invoke('add-post', post),
  deletePost:     (id)           => ipcRenderer.invoke('delete-post', id),
  updateStatus:   (id, status)   => ipcRenderer.invoke('update-status', { id, status }),
  postToX:        (id)           => ipcRenderer.invoke('post-to-x', { id }),
  saveSettings:   (s)            => ipcRenderer.invoke('save-settings', s),
  getSettings:    ()             => ipcRenderer.invoke('get-settings'),
  pickImage:      ()             => ipcRenderer.invoke('pick-image'),
  onPostsUpdated: (cb)           => ipcRenderer.on('posts-updated', cb),
})
