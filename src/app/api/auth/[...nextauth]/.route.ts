import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { NextAuthOptions } from "next-auth";

// Predefined users - in a real app, these would be in a database
const users = [
  {
    id: "1",
    name: "Expert User",
    email: "expert@example.com",
    username: "expert",
    password: "flagexpert2023",
    role: "expert"
  }
];

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        username: { label: "Username", type: "text" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        // Find user with matching username and password
        const user = users.find(
          user => 
            user.username === credentials?.username && 
            user.password === credentials?.password
        );
        
        if (user) {
          // Return user without the password
          const { password, ...userWithoutPassword } = user;
          return userWithoutPassword;
        }
        
        return null;
      }
    })
  ],
  pages: {
    signIn: "/login",
  },
  callbacks: {
    async jwt({ token, user }) {
      // Add user data to JWT token
      if (user) {
        token.id = user.id;
        token.role = user.role;
      }
      return token;
    },
    async session({ session, token }) {
      // Add user data to session
      if (token && session.user) {
        session.user.id = token.id as string;
        session.user.role = token.role as string;
      }
      return session;
    }
  },
  session: {
    strategy: "jwt",
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  secret: process.env.NEXTAUTH_SECRET || "your-fallback-secret-key",
};

const handler = NextAuth(authOptions);
export { handler as GET, handler as POST };
