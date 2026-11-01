'use client';
import { Component } from 'react';
export default class LazyErrorBoundary extends Component {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() {
    if (this.state.failed) return <div role="alert"><p>No se pudo cargar esta vista. Recarga para reintentar; tendrás que introducir el token de nuevo.</p><button type="button" onClick={() => window.location.reload()}>Recargar vista</button></div>;
    return this.props.children;
  }
}
