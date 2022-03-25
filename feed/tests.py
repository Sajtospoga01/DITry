import os
import importlib
import tempfile
from django.urls import reverse
from django.test import TestCase
from django.conf import settings

from feed.models import *
from feed.forms import *
from django.contrib.auth.models import User
from django.core.files.images import ImageFile

# some maybe unnecessary project structure tests, might be added to

class ProjectStructureTests(TestCase):

    def setUp(self):
        self.project_base_dir = os.getcwd()
        self.feed_app_dir = os.path.join(self.project_base_dir, 'feed')

    def test_feed_app_configured(self):
        is_app_configured = 'feed' in settings.INSTALLED_APPS

        self.assertTrue(is_app_configured, f"Feed app missing from INSTALLED_APPS in settings.py")

# all views tests, incredibly incomplete

class BlankViewTests(TestCase):
    # general tests
    def setUp(self):
        self.views_module = importlib.import_module('feed.views')
        self.views_module_listing = dir(self.views_module)

        self.project_urls_module = importlib.import_module('ditry_project.urls')
        user2 = UserProfile.objects.create_user(username = "alicej", email = "alice@gmail.com", password = "testpassword")
        user2.first_name = "alice"
        user2.last_name = "jones"
        user2.bio = "a bio"
        

    def test_home_view_exists(self):
        name_exists = 'home' in self.views_module_listing
        is_callable = callable(self.views_module.home)

        self.assertTrue(name_exists, f"The home() view does not exist.")
        self.assertTrue(is_callable, f"home() view is not a function")

    def test_mappings_exists(self):
        home_mapping_exists = False

        for mapping in self.project_urls_module.urlpatterns:
            if hasattr(mapping, 'name'):
                if mapping.name == 'home':
                    home_mapping_exists = True

        self.assertTrue(home_mapping_exists, f"The home url mapping could not be found.")
        self.assertEqual(reverse('feed:home'), '/feed/', f"home url lookup failed.")

    # test views without posts etc.
    def test_home_view(self):
        response = self.client.get(reverse('feed:home'))

        self.assertEqual(response.status_code, 200, f"Home page not returned with status code 200.")
        self.assertTrue('Feed empty.' in response.content.decode(), f"'Feed empty.' message not displayed.")
        self.assertTrue(not response.context['posts'], f"Non-empty posts context.")
    
    def test_category_view(self):
        self.client.login(username='alicej', password='testpassword')
        response = self.client.get(reverse('feed:show_category', kwargs={'name_category':'diy'}))
        response_body = response.content.decode()

        self.assertTrue('No diy posts yet.' in response_body, "'No diy posts yet.' message not displayed.")
        self.assertTrue(not response.context['posts'], "Non-empty posts context.")
    
    def test_trending_view(self):
        response = self.client.get(reverse('feed:trending'))
        self.assertEqual(response.status_code, 302, "Trending category page not returned with status code 302.")

    def test_trending_view_signed_in(self):
        self.client.login(username='alicej', password='testpassword')
        response = self.client.get(reverse('feed:trending'))
        response_body = response.content.decode()

        self.assertTrue('No Trending posts yet.' in response_body, "'No Trending posts yet.' message not displayed.")
        self.assertTrue(not response.context['posts'], "Non-empty posts context.")
    
    def test_logout(self):
        self.client.login(username='alicej', password='testpassword')

        response = self.client.get(reverse('feed:logout'))
        self.assertEqual(response.status_code, 302, "Should be redirected when logging out.")
        self.assertEqual(response.url, reverse('feed:home'), "Should be redirected to home page.")
        self.assertTrue('_auth_user_id' not in self.client.session, "Not properly logged out.")

class PopulatedViewTests(TestCase):
    def setUp(self):
        Helper.create_model_setup()
        self.client.login(username='alicej', password='testpassword')

    def test_home_view_with_posts(self):
        response = self.client.get(reverse('feed:home'))
        self.assertTrue("" in response.content.decode())
        self.assertEqual(Helper.num_posts_on_page(response), 2, f"Wrong number of posts passed in response.")

    def test_category_view_with_posts(self):
        post = Post.objects.create(id = 3, creator = UserProfile.objects.get(username = "alicej"), title = "food test", likes = 0)
        post.picture.save("sample_1.jpg", ImageFile(open("sample_images/sample_1.jpg", "rb")))
        Categorises.objects.create(post = post, category = Category.objects.get(name = "food")).save()

        response = self.client.get(reverse('feed:show_category', kwargs={'name_category':'diy'}))
        response_body = response.content.decode()
        self.assertTrue("diy" in response_body)
        self.assertEqual(Helper.num_posts_on_page(response), 2, "Wrong number of posts passed in response.")

        response = self.client.get(reverse('feed:show_category', kwargs={'name_category':'food'}))
        self.assertTrue("food" in response.content.decode())
        self.assertEqual(Helper.num_posts_on_page(response), 1, "Wrong number of posts passed in response.")

# all database related tests, done

class DatabaseConfigurationTests(TestCase):
    def test_databases_variable_exists(self):
        self.assertTrue(settings.DATABASES, f"Settings module doesn't have a DATABASE variable.")
        self.assertTrue('default' in settings.DATABASES, f"No default database configuration.")

class ModelTests(TestCase):
    def setUp(self):
        Helper.create_model_setup()

    def test_category_model(self):
        c_diy = Category.objects.get(name = "diy")
        self.assertTrue(c_diy.id>=0, f"Category id not autofilled.")
        c_food = Category.objects.get(name = "food")
        self.assertTrue(c_food.id > c_diy.id, f"Category id doesn't increment.")

    def test_category_slug(self):
        category = Category.objects.get_or_create(name='diy')[0]
        category.name = "Unscrupulous Nonsense"
        category.save()

        self.assertEquals('unscrupulous-nonsense', category.slug, f"When changing the name of a category, the slug attribute was not updated (correctly) to reflect this change.")

    def test_post_model(self):
        post = Post.objects.get(id = 1)
        self.assertEqual(post.title, "test", f"Expected title test, got {post.title}.")
        self.assertEqual(post.creator, UserProfile.objects.get(username = "bobs"), f"Unexpected creator.")

    def test_userprofile_model(self):
        user = UserProfile.objects.get(username = "alicej")
        self.assertEqual(user.first_name, "alice", f"Expected first name alice, got {user.first_name}.")

    def test_comment_model(self):
        comment = Comment.objects.get(id = 1)
        self.assertEqual(comment.comment, "test comment", f"Expected comment 'test comment', got {comment.comment}")
        self.assertEqual(comment.user, UserProfile.objects.get(username = "bobs"), f"Expected user bobs, got {comment.user.username}.")

    def test_likes_model(self):
        likes = Likes.objects.filter(liker = UserProfile.objects.get(username = "bobs"))
        self.assertEqual(len(likes), 2, f"Expected bobs to like 2 posts, has liked {len(likes)}.")

    def test_folder_model(self):
        folder = Folder.objects.get(id = 1)
        self.assertEqual(folder.name, "test folder", f"Expected folder name 'test folder', got {folder.name}")
        self.assertEqual(folder.user, UserProfile.objects.get(username = "bobs"), f"Expected user bobs, got {folder.user.username}.")

    def test_str_methods(self):
        category_diy = Category.objects.get(name='diy')
        user_alice = User.objects.get(username = "alicej")
        test_post = Post.objects.get(id=1)
        test_comment = Comment.objects.get(id = 1)

        self.assertEqual(str(category_diy), "diy", f"Category string method doesn't work. Expected 'diy' and got '{str(category_diy)}'.")
        self.assertEqual(str(user_alice), "alicej", f"UserProfile string method doesn't work. Expected 'alicej' and got '{str(user_alice)}'.")
        self.assertEqual(str(test_post), "test", f"Post string method doesn't work. Expected 'test' and got '{str(test_post)}'.")
        self.assertEqual(str(test_comment), "test comment", f"Comment string method doesn't work. Expected 'test comment' and got '{str(test_comment)}'.")

class QueryTests(TestCase):
    def setUp(self):
        Helper.create_model_setup()

    def test_get_comment_on_post(self):
        comments = Queries.get_comment_on_post(1)
        self.assertEqual(len(comments), 2, f"Expected 2 comments, found {len(comments)}.")
        self.assertTrue(comments.get(comment = "test comment") != None, f"Expected to find 'test comment' in comments.")

    def test_get_original(self):
        original = Queries.get_original(2)
        self.assertEqual(original.id, 1, f"Original post expected to have id 1, has id {original.id}.")

    def test_get_attempts(self):
        attempts = Queries.get_attempts(1)
        self.assertEqual(len(attempts), 1, f"Expected 1 attempt, found {len(attempts)}.")
        self.assertTrue(attempts.get(id = 2) != None, f"Expected post with id 2 to be in attempts of post 1.")

    def test_get_liked_posts(self):
        liked_posts = Queries.get_liked_posts(1)
        self.assertEqual(len(liked_posts),2, f"Expected user 1 to have liked 2 posts.")
        self.assertTrue(liked_posts.get(id=2) != None, f"Expected post 2 in user one's liked posts.")

    def test_get_post_likes(self):
        post_likes = Queries.get_post_likes(1)
        self.assertEqual(len(post_likes),2, f"Expected post 1 to have 2 likes.")
        self.assertTrue(post_likes.get(id = 1) != None, f"Expected post 1 to be liked by user bobs.")

    def test_get_category_following(self):
        category_following = Queries.get_category_following(1)
        self.assertEqual(len(category_following), 2, f"Expected user 1 to follow 2 categories.")
        self.assertTrue(category_following.get(name="diy") != None, f"Expected user 1 to be following the diy category.")

    def test_get_category_follows(self):
        follows_category = Queries.get_category_follows("diy")
        self.assertEqual(len(follows_category), 2, f"Expected two users to be following category 1.")
        self.assertTrue(follows_category.get(id = 2) != None, "Expected alicej to be following category 1.")

    def test_get_posts_in_category(self):
        posts_in_category = Queries.get_posts_in_category("diy")
        self.assertEqual(len(posts_in_category), 2, f"Expected two posts in category 'diy'.")
        self.assertTrue(posts_in_category.get(id = 1) != None, "Expected post 1 to be in category 1.")

    def test_get_category_of_post(self):
        category = Queries.get_category_of_post(1)
        self.assertEqual(category[0], Category.objects.get(id=1), f"Expected query to return category 1.")

    def test_get_user_posts(self):
        posts = Queries.get_user_posts(1)
        self.assertEqual(posts[0], Post.objects.get(id =1), f"Expected query to return post 1.")

    def test_get_user_following(self):
        following = Queries.get_user_following(2)
        self.assertEqual(following[0], UserProfile.objects.get(username = "bobs"), f"Query expected to return user bobs.")

    def test_get_user_follows(self):
        followers = Queries.get_user_follows(1)
        self.assertEqual(followers[0], UserProfile.objects.get(username = "alicej"), f"Expected query to return user alicej.")
        followers = Queries.get_user_follows(2)
        self.assertEqual(len(followers), 0, f"Expected query to return empty list.")

    def test_get_posts_in_folder(self):
        posts = Queries.get_posts_in_folder(1)
        self.assertEqual(len(posts), 1, f"Expected query to return only 1 post.")
        self.assertTrue(posts.get(id = 1) != None, f"Expected query to return post 1.")

    def test_get_user_folders(self):
        folders = Queries.get_user_folders(1)
        self.assertEqual(len(folders), 1, f"Expected query to return only 1 folder.")
        self.assertTrue(folders.get(id = 1) != None, f"Expected query to return folder 1.")


# tests for the population script, done
class PopulationScriptTests(TestCase):
    def setUp(self):
        try:
            import population_script
        except ImportError:
            raise ImportError(f"Could not import population script.")
        
        if 'populate' not in dir(population_script):
            raise NameError(f"The populate() function does not exist in the population_script module.")

        population_script.populate()

    def test_categories(self):
        categories = Category.objects.filter()
        categories_len = len(categories)
        categories_strs = map(str, categories)
        
        self.assertEqual(categories_len, 3, f"Expecting 3 categories to be created from the populate_feed module; found {categories_len}.")
        self.assertTrue('Craft' in categories_strs, f"The category 'Craft' was expected but not created by populate_feed.")
        self.assertTrue('Diy' in categories_strs, f"The category 'Diy' was expected but not created by populate_feed.")
        self.assertTrue('Cook' in categories_strs, f"The category 'Cook' was expected but not created by populate_feed.")

    def test_posts(self):
        exp_posts = {'title1': {'id':1, 'creator':1},
                    'title2': {'id':2, 'creator':2},
                    'title3': {'id':3, 'creator':1}}
        posts = Post.objects.filter()
        self.assertEqual(len(posts), len(exp_posts), f" Expected {len(exp_posts)} but got {len(posts)}.")

        for post in exp_posts:
            try:
                p = Post.objects.get(id=exp_posts[post]["id"])
            except Post.DoesNotExist:
                raise ValueError(f"The post {post} was not found in the database produced by populate_feed. ")
            self.assertEqual(post, p.title, f"The post {p.title} does not have the expected title: {post}.")
            self.assertEqual(exp_posts[post]["creator"], p.creator.id, f"The post {p.title} does not have the expected creator.")

    def test_post_objects_have_likes(self):
        posts = Post.objects.filter()
        for post in posts:
            self.assertTrue(post.likes>0, f"The post '{post.title}' has negative/zero likes.")
    
    def test_users(self):
        users = [UserProfile.objects.get(username = un) for un in ["bob", "dummy2"]]
        exp_users =[{"username":"bob", "email":"example@example.com", "first_name":"bob", "last_name":"the builder", "password":"password"}, 
        {"username":"dummy2", "email":"2@dummy.com", "first_name":"dum", "last_name":"my", "password":"dummy_password"}]
        for i in range(2):
            self.assertEqual(users[i].email, exp_users[i]["email"], f"{users[i].username}'s email is incorrect.")
            self.assertEqual(users[i].first_name, exp_users[i]["first_name"], f"{users[i].username}'s first name is incorrect.")
            self.assertEqual(users[i].last_name, exp_users[i]["last_name"], f"{users[i].username}'s last name is incorrect.")
    def test_post_category(self):
        post1 = Categorises.objects.filter(post = 1)[0]
        post2 = Categorises.objects.filter(post = 2)[0]
        post3 = Categorises.objects.filter(post = 3)[0]
        self.assertEqual(post1.category.name, "Craft",f"Post 1 has category '{post1.category}', expected 'Craft'.")
        self.assertEqual(post2.category.name, "Diy",f"Post 2 has category '{post2.category}', expected 'Diy'.")
        self.assertEqual(post3.category.name, "Cook",f"Post 3 has category '{post3.category}', expected 'Cook'.")

    def test_user_follows(self):
        follow = FollowsUser.objects.get(follower = UserProfile.objects.get(username = "bob"))
        self.assertEqual(follow.following.username, "dummy2", f"Bob not following dummy2.")

    def test_user_likes(self):
        like = Likes.objects.filter(liker = UserProfile.objects.get(username = "bob"))
        self.assertEqual(1, len(like), f"Bob has liked {len(like)} posts - expected 1.")
        self.assertEqual(like[0].liked_post.id, 1, f"Expected liked post to have id 1, was {like[0].liked_post.id}")

    def test_attempts(self):
        original = Post.objects.get(id = 2).original
        self.assertEqual(original , 1, f"Expected the original of post 2 to have id 1, has id {original}.")
        original = Post.objects.get(id=1).original
        self.assertEqual(original, -1, f"Expected post 1 to be original and so have original -1 - got {original}.")

    def test_user_follows_category(self):
        follow = FollowsCategory.objects.get(follower = UserProfile.objects.get(username = "bob"))
        self.assertEqual(follow.following.name, "Diy", f"Bob not following diy.")

    def test_comments(self):
        comment = Comment.objects.get(id = 1)
        self.assertEqual(comment.post.id, 1, f"Expected commented post to have id 1, has {comment.post}.")
        self.assertEqual(comment.user.id, 1, f"Expected commenting user to have id 1, has id {comment.user}.")
        self.assertEqual(comment.comment, "That is dope!", f"Expected comment to be 'That is dope!', was {comment.comment}.")

    def test_folders(self):
        folder = Folder.objects.get(id = 1)
        self.assertEqual(folder.name, "Folder name", f"Expected folder to have name 'Folder Name', has name {folder.name}.")
        self.assertEqual(folder.user.id, 1, f"Expected folder to have creator 1, has creator {folder.user}.")
        self.assertFalse(folder.private, f"Expected folder to be public.")

    def test_folders_post(self):
        folder_content = In_folder.objects.filter(folder = 1)
        self.assertEqual(len(folder_content), 1, f"Expected folder to contain 1 post, conttains {len(folder_content)}.")
        self.assertEqual(folder_content[0].post.id, 1, f"Expected folder to contain post 1, contains post {folder_content[0].post}.")

# admin interface tests, done
class AdminTests(TestCase):

    def setUp(self):
        User.objects.create_superuser('testAdmin', 'email@email.com', 'adminPassword123')
        self.client.login(username='testAdmin', password='adminPassword123')
        
        Helper.create_model_setup()

    def test_admin_interface_accessible(self):
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200, f"The admin interface is not accessible. Check that you didn't delete the 'admin/' URL pattern in your project's urls.py module.")

    def test_models_present(self):
        response = self.client.get('/admin/')
        response_body = response.content.decode()

        self.assertTrue('Models in the Feed application' in response_body, f"The Feed app wasn't listed on the admin interface's homepage.")
        self.assertTrue('Categories' in response_body, "Category model not found in admin interface.")
        self.assertTrue('Posts' in response_body, "Post model not found in admin interface.")
        self.assertTrue('Comments' in response_body, "Comment model not found in admin interface.")
        self.assertTrue('Folders' in response_body, "Folder model not found in admin interface.")
        self.assertTrue('Users' in response_body, "User model not found in admin interface.")

    def test_post_display(self):
        response = self.client.get('/admin/feed/post/')
        response_body = response.content.decode()

        self.assertTrue('<div class="text"><a href="?o=1">Creator</a></div>' in response_body, f"The 'Creator' column could not be found in the admin interface for the Post model.")
        self.assertTrue('<div class="text"><a href="?o=2">Title</a></div>' in response_body, f"The 'Title' column could not be found in the admin interface for the Post model.")
        self.assertTrue('<div class="text"><a href="?o=3">Likes</a></div>' in response_body, f"The 'Likes' column could not be found in the admin interface for the Post model.")
        self.assertTrue('<div class="text"><span>Comments</span></div>' in response_body, f"The 'Comments' column could not be found in the admin interface for the Post model.")

        self.assertTrue('<td class="field-title">test attempt</td>' in response_body, "Could not find post 'test attempt' in admin interface.")    

    def test_userprofile_display(self):
        response = self.client.get('/admin/feed/userprofile/')
        response_body = response.content.decode()

        self.assertTrue('<div class="text"><a href="?o=1">Username</a></div>' in response_body, f"The 'Username' column could not be found in the admin interface for the Userprofile model.")
        self.assertTrue('<div class="text"><a href="?o=2">Email address</a></div>' in response_body, f"The 'Email' column could not be found in the admin interface for the Userprofile model.")
        self.assertTrue('<div class="text"><span>Posts</span></div>' in response_body, f"The 'Posts' column could not be found in the admin interface for the Userprofile model.")
        self.assertTrue('<div class="text"><span>Follows</span></div>' in response_body, f"The 'Follows' column could not be found in the admin interface for the Userprofile model.")
        self.assertTrue('<div class="text"><span>Followers</span></div>' in response_body, f"The 'Followers' column could not be found in the admin interface for the Userprofile model.")

        self.assertTrue('bobs' in response_body, "Cound not find user bobs in admin interface.")
        self.assertTrue('<td class="field-followers">1</td>' in response_body, "Could not find bobs's number of followers (expected 1).")
    def test_category_display(self):
        response = self.client.get('/admin/feed/category/')
        response_body = response.content.decode()

        self.assertTrue('<div class="text"><span>Category</span></div>' in response_body, f"The 'Category' column could not be found in the admin interface for the Category model.")

    def test_comment_display(self):
        response = self.client.get('/admin/feed/comment/')
        response_body = response.content.decode()

        self.assertTrue('<div class="text"><a href="?o=1">Comment</a></div>' in response_body, f"The 'Comment' column could not be found in the admin interface for the Comment model.")
        self.assertTrue('<div class="text"><a href="?o=2">User</a></div>' in response_body, f"The 'User' column could not be found in the admin interface for the Comment model.")
        self.assertTrue('<div class="text"><a href="?o=3">Post</a></div>' in response_body, f"The 'Post' column could not be found in the admin interface for the Comment model.")
        self.assertTrue('<div class="text"><a href="?o=4">Likes</a></div>' in response_body, f"The 'Likes' column could not be found in the admin interface for the Comment model.")

        self.assertTrue('<th class="field-comment"><a href="/admin/feed/comment/1/change/">test comment</a></th>' in response_body, "Could not find 'test comment' in admin interface.")

    def test_folder_display(self):
        response = self.client.get('/admin/feed/folder/')
        response_body = response.content.decode()

        self.assertTrue('<div class="text"><a href="?o=1">Name</a></div>' in response_body, f"The 'Name' column could not be found in the admin interface for the Folder model.")
        self.assertTrue('<div class="text"><a href="?o=2">User</a></div>' in response_body, f"The 'User' column could not be found in the admin interface for the Folder model.")
        self.assertTrue('<div class="text"><span>Posts</span></div>' in response_body, f"The 'Posts' column could not be found in the admin interface for the Folder model.")
        self.assertTrue('<div class="text"><a href="?o=4">Private</a></div>' in response_body, f"The 'Private' column could not be found in the admin interface for the Folder model.")

        self.assertTrue('<th class="field-name"><a href="/admin/feed/folder/1/change/">test folder</a></th>' in response_body, "Could not find 'test folder' in admin interface for the Folder model.")

# forms tests
class FormTests(TestCase):
    def setUp(self):
        Helper.create_model_setup()

    def test_module_exists(self):
        project_path = os.getcwd()
        feed_app_path = os.path.join(project_path, 'feed')
        forms_module_path = os.path.join(feed_app_path, 'forms.py')

        self.assertTrue(os.path.exists(forms_module_path), "Couldn't find forms.py module.")

    def test_user_form_functionality(self):
        self.client.post(reverse('feed:register'),
            {'username': 'charlied', 'first_name': 'charlie', 'last_name': 'doe', 'email': 'charlie@gmail.com', 'password1': 'testpassword', 'password2': 'testpassword'})
        users = UserProfile.objects.filter(username = 'charlied')
        self.assertEqual(len(users), 1, "Adding a user doesn't add it to the users.")
        self.assertTrue(self.client.login(username='charlied', password='testpassword'), "Could not login with new user.")

    def test_login_form(self):
        self.client.post(reverse('feed:login'),
            {'username': 'alicej', 'password': 'testpassword'})
        response = self.client.get(reverse('feed:home'))
        response_body = response.content.decode()
        self.assertTrue("Hi, alicej" in response_body, "Can't see add post button on home page - now logged in.")

    # def test_post_form_functionality(self):
    #     self.client.login(username="alicej", password="testpassword")
    #     self.client.post(reverse('feed:add_post', {'title':'test post', 'picture': tempfile.NamedTemporaryFile(suffix=".jpg").name, 'category': 'craft'}))
    #     posts = Post.objects.filter(title = 'test post')
    #     self.assertEqual(len(posts), 1, "The post form doesn't work.")

    def test_comment_form_functionality(self):
        self.client.login(username="alicej", password="testpassword")
        self.client.post(reverse('feed:comment_on_post', kwargs={'post_id':1}), 
            {'comment':'whoop another test'})
        comments = Comment.objects.filter(comment = 'whoop another test')
        self.assertEqual(len(comments), 1, "The comment form doesn't work.")

    def test_folder_form_functionality(self): # unimplemented
        pass
# helper functions, for helping
class Helper:
    # yes I know there's a population script, but it hadn't been written yet
    def create_model_setup():
        diy = Category.objects.create(name="diy")
        diy.save()
        food = Category.objects.create(name = "food")
        food.save()

        
        user1 = UserProfile.objects.create_user(username = "bobs", email = "bob@gmail.com", password = "abc1234")
        user1.first_name = "bob"
        user1.last_name = "smith"
        user1.bio = "a bio"
        user1.profile_picture.save("sample_1.jpg", ImageFile(open("sample_images/sample_1.jpg", "rb")))
        user2 = UserProfile.objects.create_user(username = "alicej", email = "alice@gmail.com", password = "testpassword")
        user2.first_name = "alice"
        user2.last_name = "jones"
        user2.bio = "a bio"
        user2.profile_picture.save("sample_2.jpg", ImageFile(open("sample_images/sample_2.jpg", "rb")))
        

        post = Post.objects.create(id = 1, creator = user1, title = "test", likes = 0)
        post.picture.save("sample_1.jpg", ImageFile(open("sample_images/sample_1.jpg", "rb")))

        attempt_post = Post.objects.create(id = 2, creator = user2, title = "test attempt", likes =0)
        attempt_post.picture.save("sample_2.jpg", ImageFile(open("sample_images/sample_2.jpg", "rb")))
        attempt_post.original = 1
        attempt_post.save()
        

        comment1 = Comment.objects.create(post = post, user =user1, comment = "test comment")
        comment1.save()
        comment2 = Comment.objects.create(post = post, user = user2, comment = "another test comment")
        comment2.save()

        Likes.objects.create(liker = user1, liked_post = post).save()
        Likes.objects.create(liker = user2, liked_post = post).save()
        Likes.objects.create(liker = user1, liked_post = attempt_post).save()

        FollowsCategory.objects.create(follower = user1, following = diy).save()
        FollowsCategory.objects.create(follower = user1, following = food).save()
        FollowsCategory.objects.create(follower = user2, following = diy).save()

        Categorises.objects.create(post = post, category = diy).save()
        Categorises.objects.create(post = attempt_post, category = diy).save()

        FollowsUser.objects.create(follower = user2, following = user1).save()

        folder = Folder.objects.create(id = 1, name = "test folder", user = user1)
        folder.save()
        In_folder.objects.create(folder = folder, post = post).save()
    
    # gets number of posts on page when arranged in grid view
    def num_posts_on_page(response, name='posts'):
        return sum([len(row) for row in response.context[name]])

    def get_template(path_to_template):
        f = open(path_to_template, 'r')
        template_str = ""

        for line in f:
            template_str = f"{template_str}{line}"

        f.close()
        return template_str