import axios from 'axios'

const http = axios.create({ baseURL: '/api' })

export const summaryApi = {
  get: () => http.get('/summary'),
}

export const clientsApi = {
  list: () => http.get('/clients'),
  get: (id) => http.get(`/clients/${id}`),
}

export const projectsApi = {
  list: (params = {}) => http.get('/projects', { params }),
  get: (id) => http.get(`/projects/${id}`),
}

export const paymentsApi = {
  list: (params = {}) => http.get('/payments', { params }),
  get: (id) => http.get(`/payments/${id}`),
}

export const actsApi = {
  update: (id, data) => http.patch(`/acts/${id}`, data),
}

export const importApi = {
  preview: (file) => {
    const form = new FormData()
    form.append('file', file)
    return http.post('/import/preview', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  commit: (payments) => http.post('/import/commit', { payments }),
}
