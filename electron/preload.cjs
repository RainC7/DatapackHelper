// Expose a minimal, isolated preload so the renderer stays sandboxed.
const { contextBridge } = require('electron')

contextBridge.exposeInMainWorld('datapackHelper', {
	isElectron: true,
})
