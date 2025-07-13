import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useApp } from '../../contexts/AppContext';
import Button from '../common/Button';

const Header = () => {
  const { user, logout } = useAuth();
  const { toggleSidebar } = useApp();

  const handleLogout = () => {
    logout();
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center">
          <button
            onClick={toggleSidebar}
            className="text-gray-500 hover:text-gray-700 lg:hidden"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <h1 className="ml-4 text-2xl font-semibold text-gray-900 lg:ml-0">
            Welcome back, {user?.full_name || 'User'}!
          </h1>
        </div>

        <div className="flex items-center space-x-4">
          <div className="text-sm text-gray-500">
            {user?.company_name && (
              <span className="mr-4">{user.company_name}</span>
            )}
            <span>{user?.email}</span>
          </div>
          
          <Button
            onClick={handleLogout}
            variant="outline"
            size="small"
          >
            Logout
          </Button>
        </div>
      </div>
    </header>
  );
};

export default Header;