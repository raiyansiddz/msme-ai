import React, { createContext, useState, useContext, useEffect } from 'react';
import { useAuth } from './AuthContext';

const AppContext = createContext();

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

export const AppProvider = ({ children }) => {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [theme, setTheme] = useState('light');
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(false);

  // Add notification
  const addNotification = (notification) => {
    const id = Date.now();
    const newNotification = {
      id,
      ...notification,
      timestamp: new Date()
    };
    setNotifications(prev => [...prev, newNotification]);

    // Auto remove after 5 seconds
    setTimeout(() => {
      removeNotification(id);
    }, 5000);
  };

  // Remove notification
  const removeNotification = (id) => {
    setNotifications(prev => prev.filter(notif => notif.id !== id));
  };

  // Toggle sidebar
  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  // Toggle theme
  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  // Show success notification
  const showSuccess = (message) => {
    addNotification({
      type: 'success',
      message,
      title: 'Success'
    });
  };

  // Show error notification
  const showError = (message) => {
    addNotification({
      type: 'error',
      message,
      title: 'Error'
    });
  };

  // Show info notification
  const showInfo = (message) => {
    addNotification({
      type: 'info',
      message,
      title: 'Info'
    });
  };

  // Show warning notification
  const showWarning = (message) => {
    addNotification({
      type: 'warning',
      message,
      title: 'Warning'
    });
  };

  const value = {
    notifications,
    sidebarOpen,
    theme,
    dashboardData,
    loading,
    addNotification,
    removeNotification,
    toggleSidebar,
    toggleTheme,
    showSuccess,
    showError,
    showInfo,
    showWarning,
    setDashboardData,
    setLoading
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
};