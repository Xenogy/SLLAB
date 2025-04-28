import api from './api';

/**
 * Service for managing VM access control
 */
class VMAccessService {
  /**
   * Get all VMs that a user owns
   * @param {number} userId - User ID
   * @returns {Promise<Object>} - Response with user's VMs
   */
  getUserVMs(userId) {
    return api.get(`/vm-access/user/${userId}/vms`);
  }

  /**
   * Get the whitelist for a specific Proxmox node
   * @param {number} nodeId - Proxmox node ID
   * @returns {Promise<Array<number>>} - Response with whitelist VMIDs
   */
  getNodeWhitelist(nodeId) {
    return api.get(`/vm-access/node/${nodeId}/whitelist`);
  }

  /**
   * Set the whitelist for a specific Proxmox node
   * @param {number} nodeId - Proxmox node ID
   * @param {Array<number>} vmids - List of VMIDs to whitelist
   * @returns {Promise<Object>} - Response with success status
   */
  setNodeWhitelist(nodeId, vmids) {
    return api.post(`/vm-access/node/${nodeId}/whitelist`, vmids);
  }

  /**
   * Add a VMID to a node's whitelist
   * @param {number} nodeId - Proxmox node ID
   * @param {number} vmid - VMID to add
   * @returns {Promise<Object>} - Response with success status
   */
  addToNodeWhitelist(nodeId, vmid) {
    return api.post(`/vm-access/node/${nodeId}/whitelist/add/${vmid}`);
  }

  /**
   * Remove a VMID from a node's whitelist
   * @param {number} nodeId - Proxmox node ID
   * @param {number} vmid - VMID to remove
   * @returns {Promise<Object>} - Response with success status
   */
  removeFromNodeWhitelist(nodeId, vmid) {
    return api.post(`/vm-access/node/${nodeId}/whitelist/remove/${vmid}`);
  }
}

export default new VMAccessService();
