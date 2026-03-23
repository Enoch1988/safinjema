/* ─────────────────────────────────────────────────────────────
   middleware/auth.js  –  JWT authentication middleware
   ───────────────────────────────────────────────────────────── */
const jwt = require('jsonwebtoken');
const { db } = require('../db');

const SECRET = process.env.JWT_SECRET || 'dev_secret_change_in_production';

/**
 * Verifies Bearer token and attaches req.user
 */
function authenticate(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ success: false, message: 'No token provided.' });
  }
  const token = authHeader.slice(7);
  try {
    const decoded = jwt.verify(token, SECRET);
    // Confirm user still exists
    const user = db.prepare('SELECT id, name, email, role FROM users WHERE id = ?').get(decoded.id);
    if (!user) return res.status(401).json({ success: false, message: 'User not found.' });
    req.user = user;
    next();
  } catch (err) {
    return res.status(401).json({ success: false, message: 'Invalid or expired token.' });
  }
}

/**
 * Requires admin role
 */
function requireAdmin(req, res, next) {
  if (!req.user || req.user.role !== 'admin') {
    return res.status(403).json({ success: false, message: 'Admin access required.' });
  }
  next();
}

/**
 * Optional auth – doesn't fail if no token
 */
function optionalAuth(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) return next();
  try {
    const token   = authHeader.slice(7);
    const decoded = jwt.verify(token, SECRET);
    const user    = db.prepare('SELECT id, name, email, role FROM users WHERE id = ?').get(decoded.id);
    if (user) req.user = user;
  } catch (_) { /* ignore */ }
  next();
}

/** Sign a JWT for a user */
function signToken(user) {
  return jwt.sign(
    { id: user.id, email: user.email, role: user.role },
    SECRET,
    { expiresIn: process.env.JWT_EXPIRES_IN || '7d' }
  );
}

module.exports = { authenticate, requireAdmin, optionalAuth, signToken };
