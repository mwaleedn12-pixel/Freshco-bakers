import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';
import '../../shared/widgets/tilt_3d_card.dart';

/// Freshco Bakers home screen.
/// Hero banner + a grid of 3D tilt cards for featured products.
/// Product data here is placeholder — Module (Catalog) will wire this
/// up to GET /api/v1/products.
class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  static const List<_FeaturedItem> _placeholderItems = [
    _FeaturedItem('Sourdough Loaf', 'Freshly baked daily', '₨ 450', Icons.bakery_dining),
    _FeaturedItem('Chocolate Cake', 'Rich Belgian chocolate', '₨ 1,800', Icons.cake),
    _FeaturedItem('Croissant Box (6)', 'Buttery & flaky', '₨ 900', Icons.breakfast_dining),
    _FeaturedItem('Custom Cake', 'Design your own', 'Get quote', Icons.celebration),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Freshco Bakers')),
      body: CustomScrollView(
        slivers: [
          SliverToBoxAdapter(child: _HeroBanner()),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(16, 24, 16, 8),
            sliver: SliverToBoxAdapter(
              child: Text('Featured Today', style: Theme.of(context).textTheme.headlineMedium),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.all(16),
            sliver: SliverGrid(
              gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
                maxCrossAxisExtent: 260,
                mainAxisSpacing: 20,
                crossAxisSpacing: 20,
                childAspectRatio: 0.85,
              ),
              delegate: SliverChildBuilderDelegate(
                (context, index) => _ProductCard(item: _placeholderItems[index]),
                childCount: _placeholderItems.length,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _HeroBanner extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 48, horizontal: 24),
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [AppTheme.brandBrown, Color(0xFF8B5A2B)],
        ),
      ),
      child: Column(
        children: [
          Text(
            'Freshco Bakers',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  color: Colors.white,
                  fontSize: 34,
                  shadows: const [Shadow(blurRadius: 12, color: Colors.black45, offset: Offset(0, 6))],
                ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Baked fresh. Delivered warm.',
            style: TextStyle(color: Colors.white70, fontSize: 16),
          ),
          const SizedBox(height: 24),
          Tilt3DCard(
            maxTiltDegrees: 6,
            borderRadius: 24,
            child: Container(
              padding: const EdgeInsets.symmetric(vertical: 18, horizontal: 28),
              decoration: BoxDecoration(
                color: AppTheme.brandAmber,
                borderRadius: BorderRadius.circular(24),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: const [
                  Icon(Icons.storefront, color: AppTheme.brandBrown),
                  SizedBox(width: 10),
                  Text(
                    'Order Now',
                    style: TextStyle(
                      color: AppTheme.brandBrown,
                      fontWeight: FontWeight.w800,
                      fontSize: 16,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _FeaturedItem {
  const _FeaturedItem(this.name, this.subtitle, this.price, this.icon);
  final String name;
  final String subtitle;
  final String price;
  final IconData icon;
}

class _ProductCard extends StatelessWidget {
  const _ProductCard({required this.item});
  final _FeaturedItem item;

  @override
  Widget build(BuildContext context) {
    return Tilt3DCard(
      maxTiltDegrees: 12,
      borderRadius: 20,
      child: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Colors.white, AppTheme.brandCream],
          ),
        ),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 56,
              height: 56,
              decoration: BoxDecoration(
                color: AppTheme.brandAmber.withOpacity(0.2),
                shape: BoxShape.circle,
              ),
              child: Icon(item.icon, color: AppTheme.brandBrown, size: 28),
            ),
            const Spacer(),
            Text(item.name,
                style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16, color: AppTheme.brandBrown)),
            const SizedBox(height: 4),
            Text(item.subtitle, style: const TextStyle(fontSize: 12, color: Colors.black54)),
            const SizedBox(height: 8),
            Text(item.price,
                style: const TextStyle(fontWeight: FontWeight.w800, color: AppTheme.brandAmber, fontSize: 15)),
          ],
        ),
      ),
    );
  }
}
