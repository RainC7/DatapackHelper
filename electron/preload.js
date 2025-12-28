// Expose a minimal, isolated preload so the renderer stays sandboxed.
import { contextBridge } from 'electron'

contextBridge.exposeInMainWorld('datapackHelper', {
	isElectron: true,
})
