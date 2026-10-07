import 'dart:async';
import 'package:flutter/material.dart';
import '../models/models.dart';

class SearchBarWidget extends StatefulWidget {
  final Function(String) onSearch;
  final VoidCallback onClear;
  final String hintText;
  final bool autofocus;
  final IconData? prefixIcon;
  final Color? prefixIconColor;
  final bool showShadow;

  const SearchBarWidget({
    Key? key,
    required this.onSearch,
    required this.onClear,
    this.hintText = 'Search here...',
    this.autofocus = false,
    this.prefixIcon,
    this.prefixIconColor,
    this.showShadow = true,
  }) : super(key: key);

  @override
  State<SearchBarWidget> createState() => _SearchBarWidgetState();
}

class _SearchBarWidgetState extends State<SearchBarWidget> {
  Timer? _debounce;
  late TextEditingController _controller;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController();
  }

  void _onChanged(String value) {
    if (_debounce?.isActive ?? false) _debounce!.cancel();
    if (value.trim().isEmpty) {
      widget.onClear();
      return;
    }
    _debounce = Timer(const Duration(milliseconds: 600), () {
      widget.onSearch(value);
    });
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.grey.shade200),
        boxShadow: widget.showShadow
            ? [
                BoxShadow(
                  color: Colors.black.withOpacity(0.08),
                  blurRadius: 10,
                  offset: const Offset(0, 4),
                )
              ]
            : [],
      ),
      child: TextField(
        controller: _controller,
        onChanged: _onChanged,
        autofocus: widget.autofocus,
        style: const TextStyle(fontSize: 16),
        decoration: InputDecoration(
          hintText: widget.hintText,
          hintStyle: TextStyle(color: Colors.grey.shade500),
          prefixIcon: Icon(
            widget.prefixIcon ?? Icons.search,
            color: widget.prefixIconColor ?? Colors.grey.shade600,
          ),
          suffixIcon: ValueListenableBuilder<TextEditingValue>(
            valueListenable: _controller,
            builder: (context, value, child) {
              return value.text.isNotEmpty
                  ? IconButton(
                      icon: Icon(Icons.close, color: Colors.grey.shade600),
                      onPressed: () {
                        _controller.clear();
                        widget.onClear();
                      },
                    )
                  : const SizedBox.shrink();
            },
          ),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        ),
      ),
    );
  }
}

class SearchResultsWidget extends StatelessWidget {
  final List<PlaceResult> results;
  final Function(PlaceResult) onSelect;

  const SearchResultsWidget({
    Key? key,
    required this.results,
    required this.onSelect,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    if (results.isEmpty) return const SizedBox.shrink();
    return Container(
      margin: const EdgeInsets.only(top: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.08),
            blurRadius: 10,
            offset: const Offset(0, 4),
          )
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(16),
        child: ListView.separated(
          shrinkWrap: true,
          padding: EdgeInsets.zero,
          itemCount: results.length,
          separatorBuilder: (context, index) => const Divider(height: 1, indent: 56),
          itemBuilder: (context, index) {
            final p = results[index];
            return ListTile(
              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              leading: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.blue.shade50,
                  shape: BoxShape.circle,
                ),
                child: Icon(Icons.location_on, color: Colors.blue.shade600),
              ),
              title: Text(
                p.name,
                style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16),
              ),
              subtitle: Text(
                p.address,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(color: Colors.grey.shade600, fontSize: 13),
              ),
              onTap: () => onSelect(p),
            );
          },
        ),
      ),
    );
  }
}