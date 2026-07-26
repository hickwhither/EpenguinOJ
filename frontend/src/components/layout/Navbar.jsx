import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { APP_NAME } from '../../Config'
import AuthButton from '../auth/AuthButton'

export default function Navbar() {
  const [isBurgerActive, setBurgerActive] = useState(false)

  return (
    <nav className="navbar is-fixed-top" role="navigation" aria-label="main navigation">
      <a
        role="button" aria-label="menu"
        className={`navbar-burger ${isBurgerActive ? 'is-active' : ''}`}
        aria-expanded={isBurgerActive}
        onClick={() => setBurgerActive((s) => !s)}
      >
        <span aria-hidden="true"></span>
        <span aria-hidden="true"></span>
        <span aria-hidden="true"></span>
        <span aria-hidden="true"></span>
      </a>
      
      <div className={`navbar-menu ${isBurgerActive ? 'is-active' : ''}`}>
        <div className="navbar-brand">
          <NavLink className="navbar-item" to="">
            <img src="/logo.png" alt={APP_NAME}/> <strong>{APP_NAME}</strong>
          </NavLink>
        </div>
        <div className="navbar-end">
          <NavLink className="navbar-item" to="">Home</NavLink>
          <NavLink className="navbar-item" to="/problems">Problems</NavLink>
          <NavLink className="navbar-item" to="/contests">Contests</NavLink>
          <NavLink className="navbar-item" to="/judgers">Judgers</NavLink>
          <NavLink className="navbar-item" to="/about">About</NavLink>
        </div>
        <div className="navbar-end">
          <div className="navbar-item">
            <AuthButton />
          </div>
        </div>
      </div>
    </nav>
  )
}