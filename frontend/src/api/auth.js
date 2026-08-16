import http, {
  clearAccessToken,
  getAccessToken,
  saveAccessToken,
} from './http'


export function hasStoredAccessToken() {
  return Boolean(getAccessToken())
}


export async function loginUser(
  username,
  password,
) {
  clearAccessToken()

  const response = await http.post(
    '/api/auth/login',
    {
      username,
      password,
    },
  )

  saveAccessToken(
    response.data.access_token,
  )

  return response.data
}


export async function getCurrentUser() {
  const response = await http.get(
    '/api/auth/me',
  )

  return response.data
}


export function logoutUser() {
  clearAccessToken()
}