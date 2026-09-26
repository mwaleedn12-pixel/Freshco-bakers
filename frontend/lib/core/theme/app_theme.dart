import 'package:flutter/material.dart';

/// Freshco Bakers brand theme.
/// Warm amber/cream/brown palette + Material 3, tuned so elevation,
/// shadows and gradients read well with the 3D tilt-card widgets.
class AppTheme {
  static const Color brandAmber = Color(0xFFE8A33D); // warm bread-crust gold
  static const Color brandBrown = Color(0xFF5C3A21); // rich coffee brown
  static const Color brandCream = Color(0xFFFFF6E9); // dough/cream background

  static ThemeData get light => ThemeData(
        useMaterial3: true,
        brightness: Brightness.light,
        colorScheme: ColorScheme.fromSeed(
          seedColor: brandAmber,
          brightness: Brightness.light,
          primary: brandAmber,
          secondary: brandBrown,
          surface: brandCream,
        ),
        scaffoldBackgroundColor: brandCream,
        appBarTheme: const AppBarTheme(
          backgroundColor: brandBrown,
          foregroundColor: Colors.white,
          elevation: 0,
          centerTitle: true,
        ),
        textTheme: const TextTheme(
          headlineMedium: TextStyle(fontWeight: FontWeight.w800, color: brandBrown),
          titleLarge: TextStyle(fontWeight: FontWeight.w700, color: brandBrown),
          bodyMedium: TextStyle(color: Color(0xFF4A3A2A)),
        ),
        cardTheme: CardThemeData(
          elevation: 6,
          shadowColor: brandBrown.withOpacity(0.35),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        ),
      );

  static ThemeData get dark => ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        colorScheme: ColorScheme.fromSeed(
          seedColor: brandAmber,
          brightness: Brightness.dark,
        ),
      );
}
