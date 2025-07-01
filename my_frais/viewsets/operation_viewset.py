from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
from decimal import Decimal

from my_frais.models import Operation, Account
from my_frais.serializers.operation_serializer import OperationSerializer, OperationListSerializer
from my_frais.mongodb_service import mongodb_service
from my_frais.logging_service import app_logger


class OperationViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des opérations financières.
    
    Permet de créer, lire, mettre à jour et supprimer des opérations.
    Inclut des actions personnalisées pour les statistiques et la recherche.
    """
    queryset = Operation.objects.all()
    serializer_class = OperationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['compte_reference', 'created_by']
    search_fields = ['description']
    ordering_fields = ['montant', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filtrer les opérations selon l'utilisateur connecté avec optimisation"""
        user = self.request.user
        if user.is_staff:
            return Operation.objects.select_related('compte_reference', 'compte_reference__user', 'created_by').all()
        return Operation.objects.select_related('compte_reference', 'compte_reference__user', 'created_by').filter(compte_reference__user=user)
    
    def get_serializer_class(self):
        """Utiliser le serializer approprié selon l'action"""
        if self.action == 'list':
            return OperationListSerializer
        return OperationSerializer
    
    def create(self, request, *args, **kwargs):
        """Créer une opération avec debug des erreurs 400"""
        print(f"🔵 POST /operations/ - Données reçues:")
        print(f"📋 Body: {request.data}")
        print(f"👤 User: {request.user}")
        print(f"🔑 Auth: {request.auth}")
        
        try:
            serializer = self.get_serializer(data=request.data)
            
            if not serializer.is_valid():
                print(f"❌ ERREUR 400 - Validation échouée:")
                print(f"📝 Erreurs: {serializer.errors}")
                print(f"📊 Données reçues: {request.data}")
                print(f"🎯 Champs requis: {self.get_serializer().Meta.model._meta.get_fields()}")
                
                # Log de l'erreur de validation
                app_logger.log_crud_event(
                    event_type='create_failed',
                    model_name='Operation',
                    user=request.user,
                    request=request,
                    new_data=request.data,
                    old_data=None
                )
                
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            print(f"✅ SUCCÈS - Operation créée: ID {serializer.data.get('id')}")
            
            # Log de la création réussie
            app_logger.log_crud_event(
                event_type='create',
                model_name='Operation',
                object_id=serializer.data.get('id'),
                user=request.user,
                request=request,
                new_data=serializer.data,
                old_data=None
            )
            
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            
        except Exception as e:
            print(f"❌ ERREUR - Exception lors de la création: {str(e)}")
            
            # Log de l'erreur
            app_logger.log_error(
                error=e,
                user=request.user,
                request=request,
                context={'action': 'create_operation', 'data': request.data}
            )
            
            return Response({'message': 'Erreur interne du serveur.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def perform_create(self, serializer):
        """Créer une opération avec l'utilisateur connecté comme créateur"""
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Mettre à jour une opération"""
        # Sauvegarder les anciennes données pour le log
        old_data = {
            'montant': serializer.instance.montant,
            'description': serializer.instance.description,
            'compte_reference_id': serializer.instance.compte_reference.id if serializer.instance.compte_reference else None
        }
        
        serializer.save()
        
        # Log de la mise à jour
        app_logger.log_crud_event(
            event_type='update',
            model_name='Operation',
            object_id=serializer.instance.id,
            user=self.request.user,
            request=self.request,
            old_data=old_data,
            new_data=serializer.data
        )
    
    def perform_destroy(self, instance):
        """Supprimer une opération avec ajustement du solde"""
        # Sauvegarder les données avant suppression pour le log
        old_data = {
            'id': instance.id,
            'montant': instance.montant,
            'description': instance.description,
            'compte_reference_id': instance.compte_reference.id if instance.compte_reference else None,
            'created_by_id': instance.created_by.id if instance.created_by else None
        }
        
        # Utiliser la méthode delete du serializer pour ajuster le solde
        from my_frais.serializers.operation_serializer import OperationSerializer
        serializer = OperationSerializer(instance, context={'request': self.request})
        serializer.delete(instance)
        
        # Log de la suppression
        app_logger.log_crud_event(
            event_type='delete',
            model_name='Operation',
            object_id=instance.id,
            user=self.request.user,
            request=self.request,
            old_data=old_data,
            new_data=None
        )
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Obtenir les statistiques des opérations"""
        operations = self.get_queryset()
        
        # Statistiques générales
        total_operations = operations.count()
        total_montant = operations.aggregate(total=Sum('montant'))['total'] or Decimal('0.00')
        
        # Statistiques par période
        today = datetime.now().date()
        month_ago = today - timedelta(days=30)
        week_ago = today - timedelta(days=7)
        
        operations_month = operations.filter(created_at__date__gte=month_ago)
        operations_week = operations.filter(created_at__date__gte=week_ago)
        
        montant_month = operations_month.aggregate(total=Sum('montant'))['total'] or Decimal('0.00')
        montant_week = operations_week.aggregate(total=Sum('montant'))['total'] or Decimal('0.00')
        
        # Statistiques par type (positif/négatif)
        operations_positives = operations.filter(montant__gt=0)
        operations_negatives = operations.filter(montant__lt=0)
        
        montant_positif = operations_positives.aggregate(total=Sum('montant'))['total'] or Decimal('0.00')
        montant_negatif = operations_negatives.aggregate(total=Sum('montant'))['total'] or Decimal('0.00')
        
        return Response({
            'statistics': {
                'total_operations': total_operations,
                'total_montant': float(total_montant),
                'operations_30_jours': operations_month.count(),
                'montant_30_jours': float(montant_month),
                'operations_7_jours': operations_week.count(),
                'montant_7_jours': float(montant_week),
                'operations_positives': operations_positives.count(),
                'montant_positif': float(montant_positif),
                'operations_negatives': operations_negatives.count(),
                'montant_negatif': float(montant_negatif)
            }
        })
    
    @action(detail=False, methods=['get'])
    def by_account(self, request):
        """Obtenir les opérations groupées par compte"""
        operations = self.get_queryset()
        
        # Grouper par compte
        accounts_data = {}
        for operation in operations:
            account_id = operation.compte_reference.id
            account_username = operation.compte_reference.user.username
            
            if account_id not in accounts_data:
                accounts_data[account_id] = {
                    'account_id': account_id,
                    'account_username': account_username,
                    'operations_count': 0,
                    'total_montant': Decimal('0.00'),
                    'operations': []
                }
            
            accounts_data[account_id]['operations_count'] += 1
            accounts_data[account_id]['total_montant'] += operation.montant
            accounts_data[account_id]['operations'].append({
                'id': operation.id,
                'montant': float(operation.montant),
                'description': operation.description,
                'created_at': operation.created_at
            })
        
        # Convertir les montants en float pour la sérialisation JSON
        for account_data in accounts_data.values():
            account_data['total_montant'] = float(account_data['total_montant'])
        
        return Response(list(accounts_data.values()))
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Recherche avancée d'opérations"""
        query = request.query_params.get('q', '')
        min_montant = request.query_params.get('min_montant')
        max_montant = request.query_params.get('max_montant')
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        
        operations = self.get_queryset()
        
        # Filtre par texte
        if query:
            operations = operations.filter(
                Q(description__icontains=query) |
                Q(compte_reference__user__username__icontains=query)
            )
        
        # Filtre par montant
        if min_montant:
            try:
                operations = operations.filter(montant__gte=Decimal(min_montant))
            except (ValueError, TypeError):
                pass
        
        if max_montant:
            try:
                operations = operations.filter(montant__lte=Decimal(max_montant))
            except (ValueError, TypeError):
                pass
        
        # Filtre par date
        if date_debut:
            try:
                operations = operations.filter(created_at__date__gte=date_debut)
            except (ValueError, TypeError):
                pass
        
        if date_fin:
            try:
                operations = operations.filter(created_at__date__lte=date_fin)
            except (ValueError, TypeError):
                pass
        
        serializer = OperationListSerializer(operations, many=True)
        return Response({
            'query': query,
            'filters': {
                'min_montant': min_montant,
                'max_montant': max_montant,
                'date_debut': date_debut,
                'date_fin': date_fin
            },
            'results_count': operations.count(),
            'operations': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Créer plusieurs opérations en lot"""
        operations_data = request.data.get('operations', [])
        
        if not operations_data:
            return Response(
                {'error': 'Aucune opération fournie'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_operations = []
        errors = []
        
        for i, operation_data in enumerate(operations_data):
            try:
                serializer = self.get_serializer(data=operation_data)
                if serializer.is_valid():
                    operation = serializer.save(created_by=request.user)
                    created_operations.append(serializer.data)
                else:
                    errors.append({
                        'index': i,
                        'data': operation_data,
                        'errors': serializer.errors
                    })
            except Exception as e:
                errors.append({
                    'index': i,
                    'data': operation_data,
                    'errors': str(e)
                })
        
        return Response({
            'created_count': len(created_operations),
            'error_count': len(errors),
            'created_operations': created_operations,
            'errors': errors
        }, status=status.HTTP_201_CREATED if created_operations else status.HTTP_400_BAD_REQUEST) 