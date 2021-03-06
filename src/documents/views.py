from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, FormView, TemplateView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from paperless.db import GnuPG
from rest_framework.mixins import (
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import (
    GenericViewSet,
    ModelViewSet,
    ReadOnlyModelViewSet
)

from .filters import CorrespondentFilterSet, DocumentFilterSet, TagFilterSet
from .forms import UploadForm
from .models import Correspondent, Document, Log, Tag
from .serialisers import (
    CorrespondentSerializer,
    DocumentSerializer,
    LogSerializer,
    TagSerializer
)


class IndexView(TemplateView):

    template_name = "documents/index.html"

    def get_context_data(self, **kwargs):
        print(kwargs)
        print(self.request.GET)
        print(self.request.POST)
        return TemplateView.get_context_data(self, **kwargs)


class FetchView(LoginRequiredMixin, DetailView):

    model = Document

    def render_to_response(self, context, **response_kwargs):
        """
        Override the default to return the unencrypted image/PDF as raw data.
        """

        content_types = {
            Document.TYPE_PDF: "application/pdf",
            Document.TYPE_PNG: "image/png",
            Document.TYPE_JPG: "image/jpeg",
            Document.TYPE_GIF: "image/gif",
            Document.TYPE_TIF: "image/tiff",
        }

        if self.kwargs["kind"] == "thumb":
            return HttpResponse(
                GnuPG.decrypted(self.object.thumbnail_file),
                content_type=content_types[Document.TYPE_PNG]
            )

        response = HttpResponse(
            GnuPG.decrypted(self.object.source_file),
            content_type=content_types[self.object.file_type]
        )
        response["Content-Disposition"] = 'attachment; filename="{}"'.format(
            self.object.file_name)

        return response


class PushView(LoginRequiredMixin, FormView):
    """
    A crude REST-ish API for creating documents.
    """

    form_class = UploadForm

    @classmethod
    def as_view(cls, **kwargs):
        return csrf_exempt(FormView.as_view(**kwargs))

    def form_valid(self, form):
        return HttpResponse("1")

    def form_invalid(self, form):
        return HttpResponse("0")


class StandardPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page-size"
    max_page_size = 100000


class CorrespondentViewSet(ModelViewSet):
    model = Correspondent
    queryset = Correspondent.objects.all()
    serializer_class = CorrespondentSerializer
    pagination_class = StandardPagination
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filter_class = CorrespondentFilterSet
    ordering_fields = ("name", "slug")


class TagViewSet(ModelViewSet):
    model = Tag
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = StandardPagination
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filter_class = TagFilterSet
    ordering_fields = ("name", "slug")


class DocumentViewSet(RetrieveModelMixin,
                      UpdateModelMixin,
                      DestroyModelMixin,
                      ListModelMixin,
                      GenericViewSet):
    model = Document
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    pagination_class = StandardPagination
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filter_class = DocumentFilterSet
    search_fields = ("title", "correspondent__name", "content")
    ordering_fields = (
        "id", "title", "correspondent__name", "created", "modified")


class LogViewSet(ReadOnlyModelViewSet):
    model = Log
    queryset = Log.objects.all().by_group()
    serializer_class = LogSerializer
    pagination_class = StandardPagination
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering_fields = ("time",)
