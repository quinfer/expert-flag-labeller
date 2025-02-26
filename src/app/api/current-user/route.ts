import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const authHeader = request.headers.get('authorization')
  
  if (!authHeader || !authHeader.startsWith('Basic ')) {
    return NextResponse.json({ username: 'anonymous' }, { status: 200 })
  }
  
  const base64Credentials = authHeader.split(' ')[1]
  const credentials = atob(base64Credentials)
  const [username] = credentials.split(':')
  
  return NextResponse.json({ username })
}
