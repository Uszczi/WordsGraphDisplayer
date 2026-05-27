<template>
  <div class="graph-wrapper">
    <div ref="graphContainer" class="graph-container"></div>
    <div class="graph-controls">
      <div class="legend">
        <div class="legend-item">
          <span class="legend-color" style="background: #667eea;"></span>
          <span>Words</span>
        </div>
        <div class="legend-item">
          <span class="legend-color" style="background: #FF9F43;"></span>
          <span>Directors</span>
        </div>
      </div>
      <div class="zoom-control">
        <label>Zoom</label>
        <input
          v-model.number="zoomLevel"
          type="range"
          min="0.1"
          max="3"
          step="0.1"
          @input="handleZoomChange"
          class="zoom-slider"
        />
        <span class="zoom-value">{{ zoomLevel.toFixed(1) }}x</span>
      </div>
      <button @click="resetZoom">Reset Zoom</button>
      <button @click="togglePhysics">
        {{ physicsEnabled ? 'Stabilize' : 'Physics Off' }}
      </button>
      <button @click="toggleMovement" :class="{ active: movementEnabled }">
        {{ movementEnabled ? 'Freeze All' : 'Unfreeze' }}
      </button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue'
import { Network } from 'vis-network'

export default {
  name: 'GraphVisualization',
  props: {
    nodes: {
      type: Array,
      required: true
    },
    selectedNodeId: {
      type: String,
      default: null
    }
  },
  emits: ['node-selected'],
  setup(props, { emit }) {
    const graphContainer = ref(null)
    let network = null
    const physicsEnabled = ref(true)
    const zoomLevel = ref(1)
    const movementEnabled = ref(true)

    const buildGraphData = () => {
      const visNodes = []
      const visEdges = []
      const nodeMap = new Map()

      // Create nodes
      props.nodes.forEach(node => {
        nodeMap.set(node.id, node)
        // Color nodes based on type: directors get a different color
        let nodeColor = '#667eea' // default word color (purple)
        if (node.node_type === 'director') {
          nodeColor = '#FF9F43' // director color (orange)
        }
        if (props.selectedNodeId === node.id) {
          nodeColor = '#FF6B6B' // selected color (red)
        }
        
        visNodes.push({
          id: node.id,
          label: node.value,
          title: `${node.value}\nType: ${node.node_type}\nRelations: ${node.relations.length}`,
          size: Math.min(50, Math.max(25, 25 + Math.log(node.relations.length + 1) * 5)),
          color: nodeColor,
          font: {
            size: 12,
            color: 'white'
          }
        })
      })

      // Create edges (connections between nodes)
      const edgeSet = new Set()
      props.nodes.forEach(node => {
        node.relations.forEach(relation => {
          const edgeId = [node.id, relation.connect_to].sort().join('|')
          if (!edgeSet.has(edgeId)) {
            edgeSet.add(edgeId)
            visEdges.push({
              from: node.id,
              to: relation.connect_to,
              color: { color: 'rgba(200, 200, 200, 0.2)' },
              smooth: { type: 'continuous' }
            })
          }
        })
      })

      return { nodes: visNodes, edges: visEdges }
    }

    const initializeGraph = () => {
      if (!graphContainer.value) return

      const { nodes: visNodes, edges: visEdges } = buildGraphData()

      const options = {
        physics: {
          enabled: physicsEnabled.value,
          stabilization: {
            iterations: 200
          },
          barnesHut: {
            gravitationalConstant: -26000,
            centralGravity: 0.3,
            springLength: 200,
            springConstant: 0.04
          }
        },
        nodes: {
          borderWidth: 2,
          borderWidthSelected: 3,
          shadow: {
            enabled: true,
            color: 'rgba(0, 0, 0, 0.3)',
            size: 10,
            x: 5,
            y: 5
          }
        },
        edges: {
          width: 0.15,
          color: { inherit: 'from' },
          smooth: {
            type: 'continuous',
            roundness: 0.5
          }
        },
        interaction: {
          hover: true,
          tooltipDelay: 200,
          navigationButtons: true,
          keyboard: true
        },
        layout: {
          improvedLayout: false
        }
      }

      const data = {
        nodes: visNodes,
        edges: visEdges
      }

      network = new Network(graphContainer.value, data, options)

      // Handle node clicks
      network.on('click', (params) => {
        if (params.nodes.length > 0) {
          const nodeId = params.nodes[0]
          emit('node-selected', props.nodes.find(n => n.id === nodeId))
        }
      })

      // Stabilize graph
      if (physicsEnabled.value) {
        network.physics.startSimulation()
      }
    }

    const handleZoomChange = () => {
      if (network) {
        network.moveTo({
          scale: zoomLevel.value
        })
      }
    }

    const resetZoom = () => {
      if (network) {
        zoomLevel.value = 1
        network.fit()
      }
    }

    const togglePhysics = () => {
      if (network) {
        physicsEnabled.value = !physicsEnabled.value
        network.physics.enabled = physicsEnabled.value
        if (physicsEnabled.value) {
          network.physics.startSimulation()
        }
      }
    }

    const toggleMovement = () => {
      if (network) {
        movementEnabled.value = !movementEnabled.value
        // Update all nodes with fixed property
        const nodesToUpdate = network.body.nodes
        for (const nodeId in nodesToUpdate) {
          if (nodesToUpdate[nodeId]) {
            nodesToUpdate[nodeId].setOptions({
              fixed: !movementEnabled.value
            })
          }
        }
      }
    }

    watch(
      () => props.selectedNodeId,
      (newId) => {
        if (network && network.data) {
          const { nodes: visNodes } = buildGraphData()
          network.data.nodes.update(visNodes)
        }
      }
    )

    watch(
      () => props.nodes.length,
      () => {
        if (network && network.data) {
          const { nodes: visNodes, edges: visEdges } = buildGraphData()
          network.data.nodes.clear()
          network.data.edges.clear()
          network.data.nodes.add(visNodes)
          network.data.edges.add(visEdges)
          network.fit()
        }
      }
    )

    onMounted(() => {
      initializeGraph()
    })

    return {
      graphContainer,
      resetZoom,
      togglePhysics,
      toggleMovement,
      handleZoomChange,
      physicsEnabled,
      movementEnabled,
      zoomLevel
    }
  }
}
</script>

<style scoped>
.graph-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
}

.graph-container {
  flex: 1;
  width: 100%;
  height: 100%;
}

.graph-controls {
  position: absolute;
  bottom: 20px;
  left: 20px;
  display: flex;
  gap: 10px;
  align-items: center;
  z-index: 10;
  flex-wrap: wrap;
}

.legend {
  display: flex;
  gap: 15px;
  background: rgba(102, 126, 234, 0.9);
  padding: 10px 15px;
  border-radius: 4px;
  backdrop-filter: blur(10px);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: white;
  font-size: 12px;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.5);
}

.zoom-control {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(102, 126, 234, 0.9);
  padding: 10px 15px;
  border-radius: 4px;
  backdrop-filter: blur(10px);
}

.zoom-control label {
  color: white;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
}

.zoom-slider {
  width: 120px;
  height: 6px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.2);
  outline: none;
  -webkit-appearance: none;
  appearance: none;
}

.zoom-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: white;
  cursor: pointer;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

.zoom-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: white;
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

.zoom-value {
  color: white;
  font-size: 13px;
  font-weight: 500;
  min-width: 35px;
  text-align: right;
}

.graph-controls button {
  padding: 10px 15px;
  background: rgba(102, 126, 234, 0.9);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.2s;
  backdrop-filter: blur(10px);
  white-space: nowrap;
}

.graph-controls button:hover {
  background: rgba(102, 126, 234, 1);
}

.graph-controls button:active {
  background: rgba(118, 75, 162, 0.9);
}

.graph-controls button.active {
  background: rgba(255, 107, 107, 0.9);
}

.graph-controls button.active:hover {
  background: rgba(255, 107, 107, 1);
}
</style>
