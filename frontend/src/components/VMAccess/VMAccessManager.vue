<template>
  <div class="vm-access-manager">
    <h2>VM Access Management</h2>
    
    <div class="tabs">
      <div 
        class="tab" 
        :class="{ active: activeTab === 'userVMs' }" 
        @click="activeTab = 'userVMs'"
      >
        User VMs
      </div>
      <div 
        class="tab" 
        :class="{ active: activeTab === 'vmUsers' }" 
        @click="activeTab = 'vmUsers'"
      >
        VM Users
      </div>
      <div 
        class="tab" 
        :class="{ active: activeTab === 'nodeWhitelist' }" 
        @click="activeTab = 'nodeWhitelist'"
      >
        Node Whitelist
      </div>
    </div>
    
    <div class="tab-content">
      <!-- User VMs Tab -->
      <div v-if="activeTab === 'userVMs'" class="user-vms">
        <div class="form-group">
          <label for="userSelect">Select User:</label>
          <select 
            id="userSelect" 
            v-model="selectedUserId" 
            @change="loadUserVMs"
            class="form-control"
          >
            <option value="">-- Select User --</option>
            <option 
              v-for="user in users" 
              :key="user.id" 
              :value="user.id"
            >
              {{ user.username }}
            </option>
          </select>
        </div>
        
        <div v-if="selectedUserId" class="user-vms-list">
          <h3>VMs for {{ getUsernameById(selectedUserId) }}</h3>
          <div v-if="loading" class="loading">Loading...</div>
          <div v-else-if="userVMs.length === 0" class="no-data">
            No VMs found for this user.
          </div>
          <table v-else class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>VMID</th>
                <th>Name</th>
                <th>Status</th>
                <th>Proxmox Node</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="vm in userVMs" :key="vm.id">
                <td>{{ vm.id }}</td>
                <td>{{ vm.vmid }}</td>
                <td>{{ vm.name }}</td>
                <td>
                  <span :class="'status-' + vm.status.toLowerCase()">
                    {{ vm.status }}
                  </span>
                </td>
                <td>{{ vm.proxmox_node_name || 'N/A' }}</td>
                <td>
                  <button 
                    v-if="vm.owner_id !== selectedUserId"
                    @click="revokeAccess(vm.id, selectedUserId)"
                    class="btn btn-danger btn-sm"
                  >
                    Revoke Access
                  </button>
                  <span v-else class="owner-badge">Owner</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      
      <!-- VM Users Tab -->
      <div v-if="activeTab === 'vmUsers'" class="vm-users">
        <div class="form-group">
          <label for="vmSelect">Select VM:</label>
          <select 
            id="vmSelect" 
            v-model="selectedVMId" 
            @change="loadVMUsers"
            class="form-control"
          >
            <option value="">-- Select VM --</option>
            <option 
              v-for="vm in vms" 
              :key="vm.id" 
              :value="vm.id"
            >
              {{ vm.name }} (VMID: {{ vm.vmid }})
            </option>
          </select>
        </div>
        
        <div v-if="selectedVMId" class="vm-users-list">
          <h3>Users with access to {{ getVMNameById(selectedVMId) }}</h3>
          <div v-if="loading" class="loading">Loading...</div>
          <div v-else>
            <div class="add-user-form">
              <h4>Grant Access to User</h4>
              <div class="form-group">
                <label for="userToAdd">Select User:</label>
                <select 
                  id="userToAdd" 
                  v-model="userToAdd" 
                  class="form-control"
                >
                  <option value="">-- Select User --</option>
                  <option 
                    v-for="user in usersNotInVM" 
                    :key="user.id" 
                    :value="user.id"
                  >
                    {{ user.username }}
                  </option>
                </select>
              </div>
              <button 
                @click="grantAccess(selectedVMId, userToAdd)"
                :disabled="!userToAdd"
                class="btn btn-primary"
              >
                Grant Access
              </button>
            </div>
            
            <div v-if="vmUsers.length === 0" class="no-data">
              No users have access to this VM except the owner.
            </div>
            <table v-else class="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Username</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Access Granted</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in vmUsers" :key="user.id">
                  <td>{{ user.id }}</td>
                  <td>{{ user.username }}</td>
                  <td>{{ user.email }}</td>
                  <td>{{ user.role }}</td>
                  <td>{{ formatDate(user.access_granted_at) }}</td>
                  <td>
                    <button 
                      v-if="user.id !== vmOwner"
                      @click="revokeAccess(selectedVMId, user.id)"
                      class="btn btn-danger btn-sm"
                    >
                      Revoke Access
                    </button>
                    <span v-else class="owner-badge">Owner</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      
      <!-- Node Whitelist Tab -->
      <div v-if="activeTab === 'nodeWhitelist'" class="node-whitelist">
        <div class="form-group">
          <label for="nodeSelect">Select Proxmox Node:</label>
          <select 
            id="nodeSelect" 
            v-model="selectedNodeId" 
            @change="loadNodeWhitelist"
            class="form-control"
          >
            <option value="">-- Select Node --</option>
            <option 
              v-for="node in proxmoxNodes" 
              :key="node.id" 
              :value="node.id"
            >
              {{ node.name }} ({{ node.hostname }})
            </option>
          </select>
        </div>
        
        <div v-if="selectedNodeId" class="node-whitelist-content">
          <h3>Whitelist for {{ getNodeNameById(selectedNodeId) }}</h3>
          <div v-if="loading" class="loading">Loading...</div>
          <div v-else>
            <div class="add-vmid-form">
              <h4>Add VMID to Whitelist</h4>
              <div class="form-group">
                <label for="vmidToAdd">VMID:</label>
                <input 
                  id="vmidToAdd" 
                  v-model.number="vmidToAdd" 
                  type="number" 
                  min="100"
                  class="form-control"
                  placeholder="Enter VMID"
                />
              </div>
              <button 
                @click="addToWhitelist(selectedNodeId, vmidToAdd)"
                :disabled="!vmidToAdd"
                class="btn btn-primary"
              >
                Add to Whitelist
              </button>
            </div>
            
            <div v-if="nodeWhitelist.length === 0" class="no-data">
              No VMIDs in whitelist. All VMs will be synchronized.
            </div>
            <div v-else class="whitelist-items">
              <h4>Whitelisted VMIDs</h4>
              <div class="vmid-tags">
                <div 
                  v-for="vmid in nodeWhitelist" 
                  :key="vmid"
                  class="vmid-tag"
                >
                  {{ vmid }}
                  <button 
                    @click="removeFromWhitelist(selectedNodeId, vmid)"
                    class="remove-btn"
                  >
                    &times;
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import vmAccessService from '@/services/vm-access.service';
import userService from '@/services/user.service';
import vmService from '@/services/vm.service';
import proxmoxNodeService from '@/services/proxmox-node.service';

export default {
  name: 'VMAccessManager',
  data() {
    return {
      activeTab: 'userVMs',
      loading: false,
      
      // User VMs tab
      users: [],
      selectedUserId: '',
      userVMs: [],
      
      // VM Users tab
      vms: [],
      selectedVMId: '',
      vmUsers: [],
      vmOwner: null,
      userToAdd: '',
      
      // Node Whitelist tab
      proxmoxNodes: [],
      selectedNodeId: '',
      nodeWhitelist: [],
      vmidToAdd: null
    };
  },
  computed: {
    usersNotInVM() {
      // Filter out users that already have access to the VM
      const vmUserIds = this.vmUsers.map(user => user.id);
      return this.users.filter(user => !vmUserIds.includes(user.id) && user.id !== this.vmOwner);
    }
  },
  async created() {
    await this.loadUsers();
    await this.loadVMs();
    await this.loadProxmoxNodes();
  },
  methods: {
    // Common methods
    formatDate(dateString) {
      if (!dateString) return 'N/A';
      const date = new Date(dateString);
      return date.toLocaleString();
    },
    
    // User methods
    async loadUsers() {
      try {
        const response = await userService.getUsers();
        this.users = response.data.users;
      } catch (error) {
        console.error('Error loading users:', error);
        this.$toast.error('Failed to load users');
      }
    },
    getUsernameById(userId) {
      const user = this.users.find(u => u.id === userId);
      return user ? user.username : 'Unknown User';
    },
    
    // VM methods
    async loadVMs() {
      try {
        const response = await vmService.getVMs();
        this.vms = response.data.vms;
      } catch (error) {
        console.error('Error loading VMs:', error);
        this.$toast.error('Failed to load VMs');
      }
    },
    getVMNameById(vmId) {
      const vm = this.vms.find(v => v.id === vmId);
      return vm ? vm.name : 'Unknown VM';
    },
    
    // Proxmox Node methods
    async loadProxmoxNodes() {
      try {
        const response = await proxmoxNodeService.getNodes();
        this.proxmoxNodes = response.data.nodes;
      } catch (error) {
        console.error('Error loading Proxmox nodes:', error);
        this.$toast.error('Failed to load Proxmox nodes');
      }
    },
    getNodeNameById(nodeId) {
      const node = this.proxmoxNodes.find(n => n.id === nodeId);
      return node ? node.name : 'Unknown Node';
    },
    
    // User VMs tab methods
    async loadUserVMs() {
      if (!this.selectedUserId) return;
      
      this.loading = true;
      try {
        const response = await vmAccessService.getUserVMs(this.selectedUserId);
        this.userVMs = response.data.vms;
      } catch (error) {
        console.error('Error loading user VMs:', error);
        this.$toast.error('Failed to load user VMs');
      } finally {
        this.loading = false;
      }
    },
    
    // VM Users tab methods
    async loadVMUsers() {
      if (!this.selectedVMId) return;
      
      this.loading = true;
      try {
        const response = await vmAccessService.getVMUsers(this.selectedVMId);
        this.vmUsers = response.data.users;
        this.vmOwner = response.data.owner_id;
      } catch (error) {
        console.error('Error loading VM users:', error);
        this.$toast.error('Failed to load VM users');
      } finally {
        this.loading = false;
      }
    },
    async grantAccess(vmId, userId) {
      if (!vmId || !userId) return;
      
      try {
        await vmAccessService.grantVMAccess(vmId, userId);
        this.$toast.success('Access granted successfully');
        this.userToAdd = '';
        await this.loadVMUsers();
      } catch (error) {
        console.error('Error granting access:', error);
        this.$toast.error('Failed to grant access');
      }
    },
    async revokeAccess(vmId, userId) {
      if (!vmId || !userId) return;
      
      try {
        await vmAccessService.revokeVMAccess(vmId, userId);
        this.$toast.success('Access revoked successfully');
        
        // Reload the appropriate list based on active tab
        if (this.activeTab === 'userVMs') {
          await this.loadUserVMs();
        } else if (this.activeTab === 'vmUsers') {
          await this.loadVMUsers();
        }
      } catch (error) {
        console.error('Error revoking access:', error);
        this.$toast.error('Failed to revoke access');
      }
    },
    
    // Node Whitelist tab methods
    async loadNodeWhitelist() {
      if (!this.selectedNodeId) return;
      
      this.loading = true;
      try {
        const response = await vmAccessService.getNodeWhitelist(this.selectedNodeId);
        this.nodeWhitelist = response.data;
      } catch (error) {
        console.error('Error loading node whitelist:', error);
        this.$toast.error('Failed to load node whitelist');
      } finally {
        this.loading = false;
      }
    },
    async addToWhitelist(nodeId, vmid) {
      if (!nodeId || !vmid) return;
      
      try {
        await vmAccessService.addToNodeWhitelist(nodeId, vmid);
        this.$toast.success('VMID added to whitelist successfully');
        this.vmidToAdd = null;
        await this.loadNodeWhitelist();
      } catch (error) {
        console.error('Error adding to whitelist:', error);
        this.$toast.error('Failed to add VMID to whitelist');
      }
    },
    async removeFromWhitelist(nodeId, vmid) {
      if (!nodeId || !vmid) return;
      
      try {
        await vmAccessService.removeFromNodeWhitelist(nodeId, vmid);
        this.$toast.success('VMID removed from whitelist successfully');
        await this.loadNodeWhitelist();
      } catch (error) {
        console.error('Error removing from whitelist:', error);
        this.$toast.error('Failed to remove VMID from whitelist');
      }
    }
  }
};
</script>

<style scoped>
.vm-access-manager {
  padding: 20px;
}

.tabs {
  display: flex;
  margin-bottom: 20px;
  border-bottom: 1px solid #ddd;
}

.tab {
  padding: 10px 20px;
  cursor: pointer;
  border: 1px solid transparent;
  border-bottom: none;
  border-radius: 4px 4px 0 0;
  margin-right: 5px;
  background-color: #f8f9fa;
}

.tab.active {
  background-color: #fff;
  border-color: #ddd;
  border-bottom-color: #fff;
  margin-bottom: -1px;
  font-weight: bold;
}

.tab-content {
  background-color: #fff;
  padding: 20px;
  border-radius: 0 0 4px 4px;
}

.form-group {
  margin-bottom: 15px;
}

.form-control {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-danger {
  background-color: #dc3545;
  color: white;
}

.btn-sm {
  padding: 4px 8px;
  font-size: 0.875rem;
}

.btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.loading {
  text-align: center;
  padding: 20px;
  font-style: italic;
  color: #666;
}

.no-data {
  text-align: center;
  padding: 20px;
  color: #666;
  font-style: italic;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}

.data-table th,
.data-table td {
  padding: 10px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

.data-table th {
  background-color: #f8f9fa;
  font-weight: bold;
}

.status-running {
  color: green;
  font-weight: bold;
}

.status-stopped {
  color: red;
}

.status-unknown {
  color: orange;
}

.owner-badge {
  background-color: #6c757d;
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.75rem;
}

.add-user-form,
.add-vmid-form {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.vmid-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 10px;
}

.vmid-tag {
  background-color: #e9ecef;
  padding: 5px 10px;
  border-radius: 20px;
  display: flex;
  align-items: center;
}

.remove-btn {
  background: none;
  border: none;
  color: #dc3545;
  font-size: 1.2rem;
  cursor: pointer;
  margin-left: 5px;
  padding: 0 5px;
}

.remove-btn:hover {
  color: #c82333;
}
</style>
