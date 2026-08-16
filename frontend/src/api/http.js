import axios from 'axios'


const ACCESS_TOKEN_KEY =
  'security_access_token'


export function getAccessToken() {
  return sessionStorage.getItem(
    ACCESS_TOKEN_KEY,
  )
}


export function saveAccessToken(
  accessToken,
) {
  sessionStorage.setItem(
    ACCESS_TOKEN_KEY,
    accessToken,
  )
}


export function clearAccessToken() {
  sessionStorage.removeItem(
    ACCESS_TOKEN_KEY,
  )
}


const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 180000,
})


http.interceptors.request.use((config) => {
  const accessToken = getAccessToken()

  if (accessToken) {
    config.headers.Authorization =
      `Bearer ${accessToken}`
  }

  return config
})


export default http