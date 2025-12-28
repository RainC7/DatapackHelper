import { app, BrowserWindow, shell } from 'electron'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const isDev = !app.isPackaged

function createWindow() {
	const win = new BrowserWindow({
		width: 1280,
		height: 800,
		webPreferences: {
			preload: path.join(__dirname, 'preload.js'),
			contextIsolation: true,
		},
	})

	win.webContents.setWindowOpenHandler(({ url }) => {
		if (url.startsWith('http')) {
			shell.openExternal(url)
		}
		return { action: 'deny' }
	})

	if (isDev) {
		win.loadURL(process.env.VITE_DEV_SERVER_URL || 'http://localhost:3000')
		win.webContents.openDevTools({ mode: 'detach' })
	} else {
		win.loadFile(path.join(__dirname, '../dist/index.html'))
	}
}

app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
	if (process.platform !== 'darwin') {
		app.quit()
	}
})

app.on('activate', () => {
	if (BrowserWindow.getAllWindows().length === 0) {
		createWindow()
	}
})
