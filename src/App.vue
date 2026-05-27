<template>
  <div class="container">
    <header class="header">
      <h1>Words Graph Displayer</h1>
      <div class="header-controls">
        <div class="search-box">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search words..."
            @input="filterNodes"
          />
        </div>
        <button @click="loadNodes" :disabled="loading">
          {{ loading ? 'Loading...' : 'Refresh' }}
        </button>
      </div>
    </header>

    <div class="content">
      <div class="sidebar">
        <div class="stats">
          <h3>Graph Stats</h3>
          <div class="stat-item">
            <span>Total Nodes:</span>
            <strong>{{ stats.total_nodes }}</strong>
          </div>
          <div class="stat-item">
            <span>Total Relations:</span>
            <strong>{{ stats.total_relations }}</strong>
          </div>
          <div class="stat-item">
            <span>Avg Relations:</span>
            <strong>{{ stats.avg_relations?.toFixed(2) }}</strong>
          </div>
        </div>

        <div class="nodes-list">
          <h3>Nodes ({{ filteredNodes.length }})</h3>
          <div class="nodes-scroll">
            <div
              v-for="node in filteredNodes"
              :key="node.id"
              class="node-item"
              :class="{ active: selectedNodeId === node.id }"
              @click="selectNode(node)"
            >
              <span class="node-name">{{ node.value }}</span>
              <span class="node-count">{{ node.relations.length }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="main">
        <div v-if="loading" class="loading">
          <p>Loading nodes from server...</p>
        </div>
        <div v-else-if="error" class="error">
          <p>Error: {{ error }}</p>
          <button @click="loadNodes">Retry</button>
        </div>
        <div v-else class="graph-container">
          <GraphVisualization
            :nodes="nodes"
            :selected-node-id="selectedNodeId"
            @node-selected="selectNode"
          />
          <div v-if="selectedNode" class="node-details">
            <h3>{{ selectedNode.value }}</h3>
            <p class="relations-count">
              Relations: {{ selectedNode.relations.length }}
            </p>
            <div class="relations-list">
              <div
                v-for="relation in selectedNode.relations"
                :key="relation.connect_to"
                class="relation-item"
              >
                <span class="rel-type">{{ relation.rel_type }}</span>
                <span class="rel-target">{{ relation.connect_to }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { getNodes, getStats } from './api.js'
import GraphVisualization from './components/GraphVisualization.vue'

export default {
  name: 'App',
  components: {
    GraphVisualization
  },
  setup() {
    const nodes = ref([])
    const loading = ref(false)
    const error = ref(null)
    const stats = ref({
      total_nodes: 0,
      total_relations: 0,
      avg_relations: 0
    })
    const searchQuery = ref('')
    const selectedNodeId = ref(null)

    const filteredNodes = computed(() => {
      if (!searchQuery.value) return nodes.value
      const query = searchQuery.value.toLowerCase()
      return nodes.value.filter(node =>
        node.value.toLowerCase().includes(query)
      )
    })

    const selectedNode = computed(() => {
      return nodes.value.find(n => n.id === selectedNodeId.value)
    })

    const loadNodes = async () => {
      loading.value = true
      error.value = null
      try {
        const data = await getNodes()
        nodes.value = data
        const statsData = await getStats()
        stats.value = statsData
      } catch (err) {
        error.value = err.message || 'Failed to load nodes'
      } finally {
        loading.value = false
      }
    }

    const selectNode = (node) => {
      selectedNodeId.value = node.id
    }

    const filterNodes = () => {
      // Filtering is handled by computed property
    }

    onMounted(() => {
      loadNodes()
    })

    return {
      nodes,
      filteredNodes,
      selectedNode,
      selectedNodeId,
      loading,
      error,
      stats,
      searchQuery,
      loadNodes,
      selectNode,
      filterNodes
    }
  }
}
</script>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
}

.header {
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  color: white;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.header h1 {
  margin: 0 0 15px 0;
  font-size: 28px;
}

.header-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.search-box input {
  padding: 10px 15px;
  width: 300px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  font-size: 14px;
}

.search-box input::placeholder {
  color: rgba(255, 255, 255, 0.7);
}

.content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.sidebar {
  width: 280px;
  background: rgba(255, 255, 255, 0.95);
  border-right: 1px solid #ddd;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.stats {
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.stats h3 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #666;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  font-size: 13px;
}

.nodes-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 20px;
}

.nodes-list h3 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #666;
}

.nodes-scroll {
  flex: 1;
  overflow-y: auto;
  border: 1px solid #eee;
  border-radius: 4px;
}

.node-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s;
  font-size: 13px;
}

.node-item:hover {
  background-color: #f5f5f5;
}

.node-item.active {
  background-color: #667eea;
  color: white;
}

.node-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
}

.node-count {
  font-size: 11px;
  opacity: 0.7;
  margin-left: 8px;
}

.main {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.graph-container {
  flex: 1;
  display: flex;
  gap: 0;
  overflow: hidden;
}

.loading,
.error {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  color: white;
  font-size: 18px;
}

.error {
  flex-direction: column;
  gap: 20px;
}

.node-details {
  width: 250px;
  background: rgba(255, 255, 255, 0.95);
  border-left: 1px solid #ddd;
  padding: 20px;
  overflow-y: auto;
}

.node-details h3 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 16px;
}

.relations-count {
  margin: 0 0 15px 0;
  color: #666;
  font-size: 13px;
}

.relations-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.relation-item {
  display: flex;
  gap: 8px;
  padding: 8px;
  background: #f5f5f5;
  border-radius: 4px;
  font-size: 12px;
}

.rel-type {
  padding: 2px 6px;
  background: #667eea;
  color: white;
  border-radius: 3px;
  font-size: 10px;
  white-space: nowrap;
}

.rel-target {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #333;
}

@media (max-width: 1024px) {
  .sidebar {
    width: 250px;
  }

  .search-box input {
    width: 200px;
  }
}

@media (max-width: 768px) {
  .content {
    flex-direction: column;
  }

  .sidebar {
    width: 100%;
    max-height: 200px;
  }

  .main {
    flex: 1;
  }

  .node-details {
    width: 100%;
    height: 200px;
  }
}
</style>
