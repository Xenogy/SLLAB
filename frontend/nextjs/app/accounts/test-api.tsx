'use client';

import { useState, useEffect } from 'react';
import { accountsAPI, AccountListResponse, AccountListParams } from '@/lib/api';

export default function TestAccountsAPI() {
  const [accounts, setAccounts] = useState<AccountListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [params, setParams] = useState<AccountListParams>({
    limit: 10,
    offset: 0,
    sort_by: 'acc_id',
    sort_order: 'asc',
  });

  // Function to load accounts
  const loadAccounts = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await accountsAPI.getAccounts(params);
      setAccounts(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      console.error('Error loading accounts:', err);
    } finally {
      setLoading(false);
    }
  };

  // Load accounts on initial render and when params change
  useEffect(() => {
    loadAccounts();
  }, [params.limit, params.offset, params.sort_by, params.sort_order]);

  // Handle search
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadAccounts();
  };

  // Handle pagination
  const handlePrevPage = () => {
    if (params.offset && params.offset >= params.limit) {
      setParams({ ...params, offset: params.offset - params.limit });
    }
  };

  const handleNextPage = () => {
    if (accounts && accounts.total > params.offset + params.limit) {
      setParams({ ...params, offset: params.offset + params.limit });
    }
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Accounts API Test</h1>
      
      {/* Search and filters */}
      <form onSubmit={handleSearch} className="mb-4 flex gap-2">
        <input
          type="text"
          placeholder="Search accounts..."
          className="border p-2 rounded"
          value={params.search || ''}
          onChange={(e) => setParams({ ...params, search: e.target.value })}
        />
        
        <select
          className="border p-2 rounded"
          value={params.sort_by}
          onChange={(e) => setParams({ ...params, sort_by: e.target.value })}
        >
          <option value="acc_id">ID</option>
          <option value="acc_username">Username</option>
          <option value="acc_email_address">Email</option>
          <option value="acc_created_at">Created At</option>
        </select>
        
        <select
          className="border p-2 rounded"
          value={params.sort_order}
          onChange={(e) => setParams({ ...params, sort_order: e.target.value as 'asc' | 'desc' })}
        >
          <option value="asc">Ascending</option>
          <option value="desc">Descending</option>
        </select>
        
        <button type="submit" className="bg-blue-500 text-white p-2 rounded">
          Search
        </button>
      </form>
      
      {/* Filters for boolean fields */}
      <div className="mb-4 flex gap-4">
        <label className="flex items-center gap-2">
          <span>Prime:</span>
          <select
            className="border p-2 rounded"
            value={params.filter_prime === undefined ? '' : String(params.filter_prime)}
            onChange={(e) => {
              const value = e.target.value;
              setParams({ 
                ...params, 
                filter_prime: value === '' ? undefined : value === 'true' 
              });
            }}
          >
            <option value="">Any</option>
            <option value="true">Yes</option>
            <option value="false">No</option>
          </select>
        </label>
        
        <label className="flex items-center gap-2">
          <span>Locked:</span>
          <select
            className="border p-2 rounded"
            value={params.filter_lock === undefined ? '' : String(params.filter_lock)}
            onChange={(e) => {
              const value = e.target.value;
              setParams({ 
                ...params, 
                filter_lock: value === '' ? undefined : value === 'true' 
              });
            }}
          >
            <option value="">Any</option>
            <option value="true">Yes</option>
            <option value="false">No</option>
          </select>
        </label>
        
        <label className="flex items-center gap-2">
          <span>Permanently Locked:</span>
          <select
            className="border p-2 rounded"
            value={params.filter_perm_lock === undefined ? '' : String(params.filter_perm_lock)}
            onChange={(e) => {
              const value = e.target.value;
              setParams({ 
                ...params, 
                filter_perm_lock: value === '' ? undefined : value === 'true' 
              });
            }}
          >
            <option value="">Any</option>
            <option value="true">Yes</option>
            <option value="false">No</option>
          </select>
        </label>
      </div>
      
      {/* Loading and error states */}
      {loading && <p className="text-gray-500">Loading accounts...</p>}
      {error && <p className="text-red-500">Error: {error}</p>}
      
      {/* Accounts table */}
      {accounts && !loading && (
        <>
          <div className="mb-2">
            <p>
              Showing {accounts.accounts.length} of {accounts.total} accounts
              (Page {Math.floor(params.offset / params.limit) + 1})
            </p>
          </div>
          
          <table className="min-w-full border">
            <thead>
              <tr className="bg-gray-100">
                <th className="border p-2">ID</th>
                <th className="border p-2">Username</th>
                <th className="border p-2">Email</th>
                <th className="border p-2">Prime</th>
                <th className="border p-2">Locked</th>
                <th className="border p-2">Perm Locked</th>
              </tr>
            </thead>
            <tbody>
              {accounts.accounts.map((account) => (
                <tr key={account.acc_id}>
                  <td className="border p-2">{account.acc_id}</td>
                  <td className="border p-2">{account.acc_username}</td>
                  <td className="border p-2">{account.acc_email_address}</td>
                  <td className="border p-2">{account.prime ? 'Yes' : 'No'}</td>
                  <td className="border p-2">{account.lock ? 'Yes' : 'No'}</td>
                  <td className="border p-2">{account.perm_lock ? 'Yes' : 'No'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          
          {/* Pagination controls */}
          <div className="mt-4 flex gap-2">
            <button
              onClick={handlePrevPage}
              disabled={params.offset === 0}
              className={`p-2 rounded ${
                params.offset === 0 ? 'bg-gray-300' : 'bg-blue-500 text-white'
              }`}
            >
              Previous
            </button>
            <button
              onClick={handleNextPage}
              disabled={!accounts || accounts.total <= params.offset + params.limit}
              className={`p-2 rounded ${
                !accounts || accounts.total <= params.offset + params.limit
                  ? 'bg-gray-300'
                  : 'bg-blue-500 text-white'
              }`}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}
