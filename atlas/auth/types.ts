export interface AuthUser {
  id: string;
  name: string;
  email: string;
  passwordHash: string;
  salt: string;
  collegeId: string;
  createdAt: string;
}

export interface JWTPayload {
  sub: string;
  email: string;
  name: string;
  collegeId: string;
}

export interface StorageAdapter {
  getUserByEmail(email: string): Promise<AuthUser | null>;
  createUser(user: AuthUser): Promise<void>;
}
