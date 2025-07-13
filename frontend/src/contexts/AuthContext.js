import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  // Configure axios defaults
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [token]);

  // Check if user is logged in on app start
  useEffect(() => {
    const checkAuth = async () => {
      if (token) {
        try {
          const response = await axios.get(`${BACKEND_URL}/api/auth/me`);
          if (response.data.success) {
            setUser(response.data.data.user);
          } else {
            logout();
          }
        } catch (error) {
          console.error('Auth check failed:', error);
          logout();
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, [token]);

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${BACKEND_URL}/api/auth/login`, {
        email,
        password
      });

      if (response.data.success) {
        const { user, token } = response.data.data;
        setUser(user);
        setToken(token.access_token);
        localStorage.setItem('token', token.access_token);
        localStorage.setItem('refresh_token', token.refresh_token);
        return { success: true };
      } else {
        return { success: false, error: response.data.message };
      }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Login failed'
      };
    }
  };

  const register = async (userData) => {
    try {
      const response = await axios.post(`${BACKEND_URL}/api/auth/register`, userData);

      if (response.data.success) {
        const { user, token } = response.data.data;
        setUser(user);
        setToken(token.access_token);
        localStorage.setItem('token', token.access_token);
        localStorage.setItem('refresh_token', token.refresh_token);
        return { success: true };
      } else {
        return { success: false, error: response.data.message };
      }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Registration failed'
      };
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
  };

  const updateProfile = async (userData) => {
    try {
      const response = await axios.put(`${BACKEND_URL}/api/auth/me`, userData);

      if (response.data.success) {
        setUser(response.data.data.user);
        return { success: true };
      } else {
        return { success: false, error: response.data.message };
      }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Profile update failed'
      };
    }
  };

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    updateProfile,
    isAuthenticated: !!token && !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};