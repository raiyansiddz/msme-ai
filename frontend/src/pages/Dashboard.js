import React, { useState, useEffect } from 'react';
import { useApp } from '../contexts/AppContext';
import { reportsAPI, handleAPIError } from '../services/api';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Button from '../components/common/Button';

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('month');
  const { showError } = useApp();

  useEffect(() => {
    fetchDashboardData();
  }, [period]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await reportsAPI.getDashboard(period);
      setDashboardData(response.data.data.dashboard);
    } catch (error) {
      showError(handleAPIError(error));
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ title, value, icon, change, changeType }) => (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="p-5">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <span className="text-2xl">{icon}</span>
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
              <dd className="text-lg font-medium text-gray-900">{value}</dd>
            </dl>
          </div>
        </div>
        {change && (
          <div className="mt-3">
            <span className={`text-sm font-medium ${
              changeType === 'positive' ? 'text-green-600' : 
              changeType === 'negative' ? 'text-red-600' : 'text-gray-600'
            }`}>
              {changeType === 'positive' ? '↗' : changeType === 'negative' ? '↘' : '→'} {change}%
            </span>
          </div>
        )}
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  const overview = dashboardData?.overview || {};
  const kpiMetrics = dashboardData?.kpi_metrics || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <div className="flex items-center space-x-4">
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="today">Today</option>
            <option value="week">This Week</option>
            <option value="month">This Month</option>
            <option value="quarter">This Quarter</option>
            <option value="year">This Year</option>
          </select>
          <Button onClick={fetchDashboardData} variant="primary" size="small">
            Refresh
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {kpiMetrics.map((kpi, index) => (
          <StatCard
            key={index}
            title={kpi.name}
            value={kpi.unit === '₹' ? `₹${kpi.value.toLocaleString()}` : 
                   kpi.unit === '%' ? `${kpi.value.toFixed(1)}%` : 
                   kpi.value.toLocaleString()}
            icon={index === 0 ? '💰' : index === 1 ? '📊' : index === 2 ? '📄' : '👥'}
            change={kpi.change}
            changeType={kpi.change_type}
          />
        ))}
      </div>

      {/* Quick Actions */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Button variant="primary" className="h-20 flex-col">
            <span className="text-2xl mb-2">📄</span>
            Create Invoice
          </Button>
          <Button variant="secondary" className="h-20 flex-col">
            <span className="text-2xl mb-2">👥</span>
            Add Customer
          </Button>
          <Button variant="secondary" className="h-20 flex-col">
            <span className="text-2xl mb-2">📈</span>
            View Reports
          </Button>
          <Button variant="secondary" className="h-20 flex-col">
            <span className="text-2xl mb-2">🤖</span>
            Ask AI
          </Button>
        </div>
      </div>

      {/* Business Overview */}
      {overview.financial_metrics && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Financial Summary */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Financial Summary</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Total Revenue</span>
                <span className="font-medium">₹{overview.financial_metrics.total_revenue?.toLocaleString() || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Outstanding</span>
                <span className="font-medium">₹{overview.financial_metrics.total_outstanding?.toLocaleString() || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Collection Rate</span>
                <span className="font-medium">{overview.financial_metrics.collection_rate?.toFixed(1) || 0}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Growth Rate</span>
                <span className={`font-medium ${
                  (overview.financial_metrics.growth_rate || 0) > 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {overview.financial_metrics.growth_rate?.toFixed(1) || 0}%
                </span>
              </div>
            </div>
          </div>

          {/* Customer Summary */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Customer Overview</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Total Customers</span>
                <span className="font-medium">{overview.customer_metrics?.total_customers || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Active Customers</span>
                <span className="font-medium">{overview.customer_metrics?.active_customers || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">New Customers</span>
                <span className="font-medium">{overview.customer_metrics?.new_customers || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Avg. Customer Value</span>
                <span className="font-medium">₹{overview.customer_metrics?.average_customer_value?.toLocaleString() || 0}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Key Insights */}
      {overview.key_insights && overview.key_insights.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Key Insights</h3>
          <div className="space-y-2">
            {overview.key_insights.map((insight, index) => (
              <div key={index} className="flex items-start">
                <span className="text-blue-500 mr-2">•</span>
                <span className="text-sm text-gray-700">{insight}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {overview.recommendations && overview.recommendations.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-yellow-800 mb-4">💡 Recommendations</h3>
          <div className="space-y-2">
            {overview.recommendations.map((recommendation, index) => (
              <div key={index} className="flex items-start">
                <span className="text-yellow-600 mr-2">→</span>
                <span className="text-sm text-yellow-700">{recommendation}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;