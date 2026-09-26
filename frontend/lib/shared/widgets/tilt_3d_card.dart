import 'dart:math' as math;
import 'package:flutter/material.dart';

/// A card that tilts in 3D perspective as the user drags/hovers over it,
/// giving product/cake cards a "lifted off the screen" depth feel —
/// no 3D model assets or engine required, pure Flutter transforms.
class Tilt3DCard extends StatefulWidget {
  const Tilt3DCard({
    super.key,
    required this.child,
    this.maxTiltDegrees = 10,
    this.borderRadius = 20,
  });

  final Widget child;
  final double maxTiltDegrees;
  final double borderRadius;

  @override
  State<Tilt3DCard> createState() => _Tilt3DCardState();
}

class _Tilt3DCardState extends State<Tilt3DCard> {
  double _rotateX = 0;
  double _rotateY = 0;
  bool _hovering = false;

  void _updateTilt(Offset localPosition, Size size) {
    final centerX = size.width / 2;
    final centerY = size.height / 2;
    final dx = (localPosition.dx - centerX) / centerX;
    final dy = (localPosition.dy - centerY) / centerY;

    setState(() {
      _rotateY = dx * widget.maxTiltDegrees * (math.pi / 180);
      _rotateX = -dy * widget.maxTiltDegrees * (math.pi / 180);
      _hovering = true;
    });
  }

  void _reset() {
    setState(() {
      _rotateX = 0;
      _rotateY = 0;
      _hovering = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final size = Size(constraints.maxWidth, constraints.maxHeight);
        return MouseRegion(
          onEnter: (_) => setState(() => _hovering = true),
          onExit: (_) => _reset(),
          onHover: (event) => _updateTilt(event.localPosition, size),
          child: GestureDetector(
            onPanUpdate: (details) => _updateTilt(details.localPosition, size),
            onPanEnd: (_) => _reset(),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 150),
              curve: Curves.easeOut,
              transform: Matrix4.identity()
                ..setEntry(3, 2, 0.0015) // perspective depth
                ..rotateX(_rotateX)
                ..rotateY(_rotateY),
              transformAlignment: Alignment.center,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(widget.borderRadius),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(_hovering ? 0.28 : 0.14),
                    blurRadius: _hovering ? 26 : 12,
                    offset: Offset(_rotateY * 40, -_rotateX * 40 + 8),
                  ),
                ],
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(widget.borderRadius),
                child: widget.child,
              ),
            ),
          ),
        );
      },
    );
  }
}
