from django.shortcuts import render, redirect, get_object_or_404
from movies.models import Movie, Review, Rating
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Max, Sum, Count
from django.contrib.admin.views.decorators import staff_member_required

def index(request):
    search_term = request.GET.get('search')
    if search_term:
        movies = Movie.objects.filter(name__icontains=search_term)
    else:
        movies = Movie.objects.all()
    
    template_data = {}
    template_data['title'] = 'Movies'
    template_data['movies'] = movies
    return render(request, 'movies/index.html', {'template_data': template_data})

def show(request, id):
    movie = Movie.objects.get(id=id)
    reviews = Review.objects.filter(movie=movie)
    average_rating = Rating.objects.filter(movie=movie).aggregate(Avg('value'))['value__avg']
    user_rating = None
    if request.user.is_authenticated:
        user_rating = Rating.objects.filter(movie=movie, user=request.user).first()

    template_data = {}
    template_data['title'] = movie.name
    template_data['movie'] = movie
    template_data['reviews'] = reviews
    template_data['average_rating'] = average_rating
    template_data['rating_count'] = Rating.objects.filter(movie=movie).count()
    template_data['user_rating'] = user_rating
    template_data['rating_options'] = [1, 2, 3, 4, 5]
    return render(request, 'movies/show.html', {'template_data': template_data})

def top_commenter(request):
    top_user = (
        Review.objects
        .values('user__username')
        .annotate(comment_count=Count('id'))
        .order_by('-comment_count', 'user__username')
        .first()
    )

    template_data = {}
    template_data['title'] = 'Top Commenter'
    template_data['top_user'] = top_user

    return render(request, 'movies/top_commenter.html', {'template_data': template_data})


@login_required
def create_review(request, id):
    if request.method == 'POST' and request.POST['comment'] !='':
        movie = Movie.objects.get(id=id)
        review = Review()
        review.comment = request.POST['comment']
        review.movie = movie
        review.user = request.user
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)
    
@login_required
def submit_rating(request, id):
    if request.method != 'POST':
        return redirect('movies.show', id=id)
    
    movie = get_object_or_404(Movie, id=id)
    try:
        rating_value = int(request.POST.get('rating', ''))
    except (ValueError, TypeError):
        return redirect('movies.show', id=id)
    
    if rating_value < 1 or rating_value > 5:
        return redirect('movies.show', id=id)

    Rating.objects.update_or_create(
        movie=movie,
        user=request.user,
        defaults={'value': rating_value}
    )

    return redirect('movies.show', id=id)

@login_required
def edit_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.user != review.user:
        return redirect('movies.show', id=id)
    
    if request.method == 'GET':
        template_data= {}
        template_data['title']= 'Edit Review'
        template_data['review'] = review
        return render(request, 'movies/edit_review.html', {'template_data': template_data})
    
    elif request.method == 'POST' and request.POST['comment'] != '':
        review = Review.objects.get(id=review_id)
        review.comment = request.POST['comment']
        review.save()
        return redirect('movies.show', id=id)

    else:
        return redirect('movies.show', id=id)
    
@login_required
def delete_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    review.delete()
    return redirect ('movies.show', id=id)

def report_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    review.delete()
    return redirect ('movies.show', id=id)

@login_required
@staff_member_required
def admin_stats(request):
    reviewed_counts = Movie.objects.annotate(review_count=Count('review'))
    max_reviews = reviewed_counts.aggregate(max_count=Max('review_count'))['max_count'] or 0
    most_reviewed_movies = reviewed_counts.filter(review_count=max_reviews)

    purchased_counts = Movie.objects.annotate(purchase_count=Sum('item__quantity'))
    max_purchases = purchased_counts.aggregate(max_count=Max('purchase_count'))['max_count'] or 0
    most_purchased_movies = purchased_counts.filter(purchase_count=max_purchases)

    template_data = {}
    template_data['title'] = 'Admin Statistics'
    template_data['most_reviewed_movies'] = most_reviewed_movies
    template_data['most_purchased_movies'] = most_purchased_movies
    return render(request, 'movies/admin_stats.html', {'template_data': template_data})
