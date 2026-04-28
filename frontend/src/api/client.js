import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// Inject JWT token into every request automatically
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// On 401 — clear token and redirect to login
client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ── Auth ─────────────────────────────────────────────────────
export const login    = (data) => client.post('/auth/login', data)
export const register = (data) => client.post('/auth/register', data)
export const getMe    = ()     => client.get('/auth/me')

// ── Predictions ───────────────────────────────────────────────
export const predictSingle   = (data) => client.post('/predict', data)
export const predictBatch    = (file) => {
  const form = new FormData()
  form.append('file', file)
  return client.post('/predict-batch', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,  // batch can take longer
  })
}
export const getTemplate              = ()     => client.get('/template', { responseType: 'blob' })
export const getAssessment            = (id)   => client.get(`/assessment/${id}`)
export const getBatch                 = (id)   => client.get(`/batch/${id}`)
export const exportAssessmentPdf      = (id)   => client.get(`/assessment/${id}/pdf`, { responseType: 'blob' })
export const exportBatchPdf           = (id)   => client.get(`/batch/${id}/pdf`,      { responseType: 'blob' })
export const deleteAssessment         = (id)   => client.delete(`/assessment/${id}`)
export const deleteBatch              = (id)   => client.delete(`/batch/${id}`)
export const deleteStudentAssessments = (id)   => client.delete(`/student/${id}`)

// ── Dashboard ─────────────────────────────────────────────────
export const getDashboardStats   = ()   => client.get('/dashboard/stats')
export const getDashboardHistory = ()   => client.get('/dashboard/history')
export const getStudentHistory   = (id) => client.get(`/dashboard/student/${id}`)

export default client
