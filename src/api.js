import axios from 'axios'

const API_URL = 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

export const getNodes = async () => {
  try {
    const response = await api.get('/nodes')
    return response.data.nodes || []
  } catch (error) {
    console.error('Error fetching nodes:', error)
    throw error
  }
}

export const getNodeById = async (nodeId) => {
  try {
    const response = await api.get(`/nodes/${nodeId}`)
    return response.data
  } catch (error) {
    console.error(`Error fetching node ${nodeId}:`, error)
    throw error
  }
}

export const getStats = async () => {
  try {
    const response = await api.get('/stats')
    return response.data
  } catch (error) {
    console.error('Error fetching stats:', error)
    throw error
  }
}

export default api
