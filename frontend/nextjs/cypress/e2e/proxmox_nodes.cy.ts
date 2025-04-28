describe('Proxmox Nodes', () => {
  beforeEach(() => {
    // Log in
    cy.login('admin', 'admin_password')
    
    // Visit the Proxmox nodes page
    cy.visit('/proxmox-nodes')
  })
  
  it('should display a list of Proxmox nodes', () => {
    // Check the page title
    cy.contains('h1', 'Proxmox Nodes').should('be.visible')
    
    // Check the node list
    cy.get('[data-testid="node-row"]').should('have.length.at.least', 1)
  })
  
  it('should add a new Proxmox node', () => {
    // Click the add node button
    cy.contains('button', 'Add Node').click()
    
    // Fill the form
    cy.get('[name="name"]').type('test-node')
    cy.get('[name="hostname"]').type('test.example.com')
    cy.get('[name="port"]').clear().type('8006')
    
    // Submit the form
    cy.contains('button', 'Add Node').click()
    
    // Check the API key dialog
    cy.contains('API Key for test-node').should('be.visible')
    cy.contains('button', 'Close').click()
    
    // Check the new node is in the list
    cy.contains('[data-testid="node-row"]', 'test-node').should('be.visible')
  })
  
  it('should edit a Proxmox node', () => {
    // Find the first node
    cy.get('[data-testid="node-row"]').first().as('firstNode')
    
    // Click the edit button
    cy.get('@firstNode').find('[aria-label="Edit"]').click()
    
    // Update the name
    cy.get('[name="name"]').clear().type('updated-node')
    
    // Submit the form
    cy.contains('button', 'Save Changes').click()
    
    // Check the node was updated
    cy.contains('[data-testid="node-row"]', 'updated-node').should('be.visible')
  })
  
  it('should delete a Proxmox node', () => {
    // Find the first node
    cy.get('[data-testid="node-row"]').first().as('firstNode')
    
    // Get the node name
    cy.get('@firstNode').find('[data-testid="node-name"]').invoke('text').as('nodeName')
    
    // Click the delete button
    cy.get('@firstNode').find('[aria-label="Delete"]').click()
    
    // Confirm deletion
    cy.on('window:confirm', () => true)
    
    // Check the node was deleted
    cy.get('@nodeName').then((nodeName) => {
      cy.contains('[data-testid="node-row"]', nodeName).should('not.exist')
    })
  })
})
