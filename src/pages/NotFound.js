import React from 'react';
import { Link } from 'react-router-dom';

/**
 * The catch-all route. Previously any unknown URL fell through to the router's
 * index and rendered the homepage, so a typo looked like a working page.
 */
const NotFound = () => (
  <div className="bg-black text-white min-h-screen flex items-center justify-center px-6">
    <div className="max-w-md text-center">
      <p className="text-6xl font-bold mb-4 text-white/20">404</p>
      <h1 className="text-2xl font-bold mb-3">Page not found</h1>
      <p className="text-white/40 text-sm mb-8">
        That page does not exist. It may have moved, or the link may be wrong.
      </p>
      <div className="flex flex-wrap gap-3 justify-center">
        <Link to="/" className="px-6 py-3 bg-white text-black text-sm font-medium hover:bg-gray-100 transition-colors">
          Go home
        </Link>
        <Link to="/contact" className="px-6 py-3 border border-white/20 text-sm hover:bg-white/5 transition-colors">
          Contact us
        </Link>
      </div>
    </div>
  </div>
);

export default NotFound;
