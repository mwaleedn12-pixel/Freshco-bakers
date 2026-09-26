import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../features/home/home_screen.dart';

/// Central route table. Each feature module registers its own routes
/// here as it is built (auth, catalog, cart, checkout, orders, admin, pos...).
final GoRouter appRouter = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(
      path: '/',
      name: 'home',
      builder: (context, state) => const HomeScreen(),
    ),
    // Future routes, added module by module:
    // GoRoute(path: '/login', name: 'login', builder: ...),
    // GoRoute(path: '/catalog', name: 'catalog', builder: ...),
    // GoRoute(path: '/product/:id', name: 'product', builder: ...),
    // GoRoute(path: '/cart', name: 'cart', builder: ...),
    // GoRoute(path: '/checkout', name: 'checkout', builder: ...),
    // GoRoute(path: '/orders', name: 'orders', builder: ...),
    // GoRoute(path: '/admin', name: 'admin', builder: ...),
    // GoRoute(path: '/pos', name: 'pos', builder: ...),
  ],
);
