const API = import.meta.env.VITE_API_URL || '/api'

function getToken() {
  return localStorage.getItem('dot_token')
}

export async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) }
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = headers['Content-Type'] || 'application/json'
  }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`

  let res
  try {
    res = await fetch(`${API}${path}`, { ...options, headers })
  } catch {
    throw new Error('Сервер недоступен. Запустите backend: uvicorn app.main:app --port 8000')
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    const msg = err.detail
    const text = Array.isArray(msg)
      ? msg.map((e) => e.msg || JSON.stringify(e)).join(', ')
      : typeof msg === 'string'
        ? msg
        : 'Ошибка запроса'
    throw new Error(text)
  }
  if (res.status === 204) return null
  return res.json()
}

export async function login(email, password) {
  const body = new URLSearchParams({ username: email, password })
  let res
  try {
    res = await fetch(`${API}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body,
    })
  } catch {
    throw new Error('Сервер недоступен. Запустите backend на порту 8000')
  }
  if (!res.ok) throw new Error('Неверный email или пароль')
  const data = await res.json()
  localStorage.setItem('dot_token', data.access_token)
  return data
}

export function logout() {
  localStorage.removeItem('dot_token')
  localStorage.removeItem('dot_company_id')
}

export async function uploadAvatar(file) {
  const token = getToken()
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API}/auth/me/avatar`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  })
  if (!res.ok) throw new Error('Не удалось загрузить аватар')
  return res.json()
}

export async function uploadLogo(companyId, file) {
  const token = getToken()
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API}/companies/${companyId}/logo`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  })
  if (!res.ok) throw new Error('Не удалось загрузить логотип')
  return res.json()
}

export async function uploadImage(companyId, file) {
  const token = getToken()
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API}/companies/${companyId}/upload`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  })
  if (!res.ok) throw new Error('Не удалось загрузить изображение')
  return res.json()
}
