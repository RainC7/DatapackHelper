import { app, BrowserWindow, protocol, shell } from 'electron'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const isDev = !app.isPackaged

protocol.registerSchemesAsPrivileged([
	{
		scheme: 'app',
		privileges: {
			standard: true,
			secure: true,
			supportFetchAPI: true,
			corsEnabled: true,
		},
	},
])

function createWindow() {
	const win = new BrowserWindow({
		width: 1280,
		height: 800,
		webPreferences: {
			preload: path.join(__dirname, 'preload.cjs'),
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
		win.loadURL('app://./index.html')
	}
}

function registerAppProtocol() {
	const distPath = path.join(__dirname, '../dist')
	protocol.registerFileProtocol('app', (request, callback) => {
		const url = new URL(request.url)
		const pathname = decodeURIComponent(url.pathname)
		const relativePath = pathname.replace(/^\/+/, '')
		const filePath = relativePath === ''
			? path.join(distPath, 'index.html')
			: path.extname(relativePath) === ''
				? path.join(distPath, relativePath, 'index.html')
				: path.join(distPath, relativePath)
		callback({ path: filePath })
	})
}

app.whenReady().then(() => {
	if (!isDev) {
		registerAppProtocol()
	}
	createWindow()
})

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
