import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useApp } from '../../contexts/AppContext';

const Sidebar = () => {
  const location = useLocation();
  const { sidebarOpen, toggleSidebar } = useApp();

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: '📊' },
    { name: 'Invoices', href: '/invoices', icon: '📄' },
    { name: 'Customers', href: '/customers', icon: '👥' },
    { name: 'Reports', href: '/reports', icon: '📈' },
    { name: 'AI Assistant', href: '/ai-assistant', icon: '🤖' },
    { name: 'Settings', href: '/settings', icon: '⚙️' }
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <div className={`${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0`}>
      <div className="flex items-center justify-center h-16 bg-indigo-600">
        <span className="text-white text-xl font-bold">MSME SaaS</span>
      </div>
      
      <nav className="mt-8">
        <div className="px-2 space-y-1">
          {navigation.map((item) => (
            <Link
              key={item.name}
              to={item.href}
              className={`${
                isActive(item.href)
                  ? 'bg-indigo-100 text-indigo-900'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              } group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors duration-150`}
              onClick={() => window.innerWidth < 1024 && toggleSidebar()}
            >
              <span className="mr-3 text-lg">{item.icon}</span>
              {item.name}
            </Link>
          ))}
        </div>
      </nav>
    </div>
  );
};

export default Sidebar;