from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect

from .forms import RouteForm
from .models import Route, RouteImage

import os
import re
import unicodedata


def _slugify_simple(value: str, allow_unicode: bool = False) -> str:
    """
    Lightweight slugify: lowercase, spaces -> '-', remove anything not alnum, dash, or underscore.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value.lower())
    value = re.sub(r"[\s-]+", "-", value).strip("-")
    return value or "untitled"


def _normalized_ext(original_name: str) -> str:
    """
    Lowercase extension; fall back to .jpg if missing/unknown.
    """
    ext = os.path.splitext(original_name)[1].lower()
    if ext in {".jpg", ".jpeg"}: return ".jpg"
    if ext in {".png"}: return ".png"
    if ext in {".webp"}: return ".webp"
    if ext in {".gif"}: return ".gif"
    return ".jpg"


def route_list(request):
    routes = Route.objects.select_related("author").prefetch_related("images")
    return render(request, "routes/route_list.html", {"routes": routes})


def route_detail(request, pk: int):
    route = get_object_or_404(
        Route.objects.select_related("author").prefetch_related("images"),
        pk=pk
    )
    return render(request, "routes/route_detail.html", {"route": route})


@login_required
def route_create(request):
    if request.method == "POST":
        form = RouteForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            files = form.cleaned_data.get("images") or []

            # Save route first (need author/title to name files)
            route = form.save(commit=False)
            route.author = request.user
            route.save()

            user_slug = _slugify_simple(request.user.username or "user")
            title_slug = _slugify_simple(route.title or "route")

            for idx, f in enumerate(files, start=1):
                ext = _normalized_ext(getattr(f, "name", "") or "")
                # NOTE: plain index (no zero padding)
                new_name = f"{user_slug}_{title_slug}_{idx}{ext}"
                f.name = new_name  # ensures storage uses this filename
                RouteImage.objects.create(route=route, image=f, order=idx)

            messages.success(request, "Route added!")
            return redirect("routes:detail", pk=route.pk)
        # fall through
    else:
        form = RouteForm(user=request.user)

    return render(request, "routes/route_form.html", {"form": form})
