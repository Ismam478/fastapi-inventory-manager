/**
 * Admin Dashboard Module
 * Handles product management, token authorization, and UI interactions
 */

// ===== STATE MANAGEMENT =====
let products = [];
let selectedProductId = null;

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', () => {
    checkAuthentication();
    loadProducts();
    attachEventListeners();
});

/**
 * Check if user is authenticated
 * Redirect to login if no token is found
 */
function checkAuthentication() {
    const token = localStorage.getItem('access_token');
    console.log('Token check:', token ? 'Token found' : 'No token found');
    if (!token) {
        console.log('Redirecting to login...');
        window.location.href = '/login';
    }
}

/**
 * Get authorization headers with Bearer token
 * @returns {Object} Headers object with Authorization
 */
function getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
}

// ===== PRODUCT FETCHING =====
/**
 * Load all products from admin endpoint
 */
async function loadProducts() {
    const loadingState = document.getElementById('loadingState');
    const errorState = document.getElementById('errorState');
    const tableContainer = document.getElementById('tableContainer');
    const emptyState = document.getElementById('emptyState');

    try {
        const response = await fetch('/admin/', {
            method: 'GET',
            headers: getAuthHeaders()
        });

        if (response.status === 401) {
            // Token expired or invalid
            localStorage.removeItem('access_token');
            window.location.href = '/login';
            return;
        }

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        products = data.products || [];

        loadingState.classList.add('hidden');

        if (products.length === 0) {
            emptyState.classList.remove('hidden');
        } else {
            tableContainer.classList.remove('hidden');
            renderProductTable();
        }
    } catch (error) {
        console.error('Error loading products:', error);
        loadingState.classList.add('hidden');
        errorState.classList.remove('hidden');
        errorState.querySelector('div').textContent = `Failed to load products: ${error.message}`;
    }
}

/**
 * Render products in the table
 */
function renderProductTable() {
    const tableBody = document.getElementById('productTableBody');
    tableBody.innerHTML = '';

    products.forEach(product => {
        const row = document.createElement('tr');
        row.className = 'border-b border-gray-200 hover:bg-gray-50 transition';
        row.innerHTML = `
            <td class="px-6 py-4 text-sm font-semibold text-gray-900">${escapeHtml(product.name)}</td>
            <td class="px-6 py-4 text-sm text-gray-600">${escapeHtml(product.category || 'N/A')}</td>
            <td class="px-6 py-4 text-sm font-semibold text-gray-900">$${product.price.toFixed(2)}</td>
            <td class="px-6 py-4 text-sm text-gray-600">${product.quantity}</td>
            <td class="px-6 py-4 text-sm">
                <span class="px-3 py-1 rounded-full text-xs font-semibold ${
                    product.in_stock 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                }">
                    ${product.in_stock ? 'In Stock' : 'Out of Stock'}
                </span>
            </td>
            <td class="px-6 py-4 text-sm text-center">
                <button
                    onclick="openDeleteModal(${product.id})"
                    class="bg-red-600 hover:bg-red-700 text-white font-semibold py-1 px-3 rounded transition text-xs"
                >
                    Delete
                </button>
            </td>
        `;
        tableBody.appendChild(row);
    });
}

// ===== ADD PRODUCT =====
/**
 * Handle add product form submission
 */
async function handleAddProduct(e) {
    e.preventDefault();

    const formError = document.getElementById('formError');
    const formSuccess = document.getElementById('formSuccess');
    const addProductBtn = document.getElementById('addProductBtn');

    formError.classList.add('hidden');
    formSuccess.classList.add('hidden');

    const productData = {
        name: document.getElementById('productName').value.trim(),
        price: parseFloat(document.getElementById('productPrice').value),
        quantity: parseInt(document.getElementById('productQuantity').value),
        description: document.getElementById('productDescription').value.trim() || '',
        category: document.getElementById('productCategory').value.trim() || null,
        in_stock: parseInt(document.getElementById('productQuantity').value) > 0
    };

    // Validation
    if (!productData.name || productData.price < 0 || productData.quantity < 0) {
        showFormError('Please fill in all required fields with valid values.');
        return;
    }

    addProductBtn.disabled = true;
    addProductBtn.textContent = 'Adding...';

    try {
        const response = await fetch('/admin/add_products', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(productData)
        });

        if (response.status === 401) {
            localStorage.removeItem('access_token');
            window.location.href = '/login';
            return;
        }

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Failed to add product');
        }

        showFormSuccess('Product added successfully!');
        document.getElementById('addProductForm').reset();
        
        // Reload products
        setTimeout(() => {
            loadProducts();
        }, 800);
    } catch (error) {
        console.error('Error adding product:', error);
        showFormError(`Error: ${error.message}`);
    } finally {
        addProductBtn.disabled = false;
        addProductBtn.textContent = 'Add Product';
    }
}

// ===== DELETE PRODUCT =====
/**
 * Open delete confirmation modal
 * @param {number} productId - Product ID to delete
 */
function openDeleteModal(productId) {
    selectedProductId = productId;
    document.getElementById('deleteModal').classList.remove('hidden');
}

/**
 * Close delete confirmation modal
 */
function closeDeleteModal() {
    selectedProductId = null;
    document.getElementById('deleteModal').classList.add('hidden');
}

/**
 * Confirm and execute product deletion
 */
async function confirmDelete() {
    if (!selectedProductId) return;

    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    confirmDeleteBtn.disabled = true;
    confirmDeleteBtn.textContent = 'Deleting...';

    try {
        const response = await fetch(`/admin/delete_products/${selectedProductId}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });

        if (response.status === 401) {
            localStorage.removeItem('access_token');
            window.location.href = '/login';
            return;
        }

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Failed to delete product');
        }

        closeDeleteModal();
        loadProducts();
    } catch (error) {
        console.error('Error deleting product:', error);
        alert(`Error: ${error.message}`);
    } finally {
        confirmDeleteBtn.disabled = false;
        confirmDeleteBtn.textContent = 'Delete';
    }
}

// ===== LOGOUT =====
/**
 * Handle user logout
 */
function handleLogout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('token_type');
    window.location.href = '/login';
}

// ===== FORM TOGGLES & MESSAGES =====
/**
 * Display form error message
 * @param {string} message - Error message
 */
function showFormError(message) {
    const formError = document.getElementById('formError');
    formError.textContent = message;
    formError.classList.remove('hidden');
}

/**
 * Display form success message
 * @param {string} message - Success message
 */
function showFormSuccess(message) {
    const formSuccess = document.getElementById('formSuccess');
    formSuccess.textContent = message;
    formSuccess.classList.remove('hidden');
}

/**
 * Toggle add product form visibility
 */
function toggleAddProductForm() {
    const form = document.getElementById('addProductForm');
    const toggleBtn = document.getElementById('toggleFormBtn');
    
    if (form.style.display === 'none') {
        form.style.display = 'block';
        toggleBtn.textContent = '▼ Collapse';
    } else {
        form.style.display = 'none';
        toggleBtn.textContent = '▶ Expand';
    }
}

// ===== UTILITY FUNCTIONS =====
/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ===== EVENT LISTENERS =====
/**
 * Attach all event listeners
 */
function attachEventListeners() {
    // Form submission
    document.getElementById('addProductForm').addEventListener('submit', handleAddProduct);

    // Form toggle
    document.getElementById('toggleFormBtn').addEventListener('click', toggleAddProductForm);

    // Logout
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);

    // Delete modal
    document.getElementById('cancelDeleteBtn').addEventListener('click', closeDeleteModal);
    document.getElementById('confirmDeleteBtn').addEventListener('click', confirmDelete);

    // Close modal when clicking outside
    document.getElementById('deleteModal').addEventListener('click', (e) => {
        if (e.target === document.getElementById('deleteModal')) {
            closeDeleteModal();
        }
    });
}
