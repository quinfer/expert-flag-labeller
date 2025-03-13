'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";

// Define multiple valid users
const VALID_USERS = [
  { username: "Declan", password: "2HVrOj37rYdUivy+", name: "Declan French" },
  { username: "Dominic", password: "97Z+FIK/gdBC+cLo", name: "Dominic Bryan" },
  { username: "Barry", password: "5aHt5wjEZ7Bbwnd/", name: "Barry Quinn" },
  { username: "Brandon", password: "s+tCGH8K4phMwY1T", name: "Brandon Cochrane"},
  { username: "Byron", password: "jR5vT8yM3pB9kL7+", name: "Byron Graham" }
];

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // Find matching user
    const user = VALID_USERS.find(
      user => user.username === username && user.password === password
    );

    if (user) {
      // Store authentication in localStorage with the user's name and username
      localStorage.setItem('isAuthenticated', 'true');
      localStorage.setItem('user', JSON.stringify({ 
        name: user.name,
        username: user.username 
      }));
      
      // Redirect to the main application page
      router.push('/');
    } else {
      setError('Invalid username or password');
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <Card className="w-full max-w-md">
        <CardHeader>
          <h1 className="text-2xl font-bold text-center">Expert Flag Labeller</h1>
          <p className="text-center text-gray-500">Please log in to continue</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full p-2 border rounded"
                placeholder="Enter username"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full p-2 border rounded"
                placeholder="Enter password"
                required
              />
            </div>
            {error && <p className="text-red-500 text-sm">{error}</p>}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Logging in...' : 'Login'}
            </Button>
          </form>
          
          {/* Removed the login instructions */}
        </CardContent>
      </Card>
    </div>
  );
}
