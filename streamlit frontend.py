import streamlit as st # type: ignore
import requests
import json
# Initialize state if it doesn't exist
#if 'current_page' not in st.session_state:
#    st.session_state['current_page'] = 'home'

def show_login():
    #global user_data, user_id
    st.title("Log In")
    st.write("Please log in to your account")
    email = st.text_input("Enter Email:")
    password = st.text_input("Enter Password:")

    if st.button("Login"):
        if (not email or not password):
            st.error("Please fill in all fields")
        else:
            payload = {"email":email, "password": password}
            try:
                response = requests.post(base_url + "login", json=payload)
                response.raise_for_status()
                user_data = response.json()
                #user_id = user_data['user_id']
                st.session_state['user'] = user_data
                st.session_state['current_page'] = 'home'
            except requests.exceptions.RequestException as e:
                print(f"Error with login credentials: {e}")
                st.error("Error with login credentials")
            except json.JSONDecodeError:
                print("Error decoding JSON response.")
    
    if st.button("Don't have an account? Sign up!"):
        st.session_state['current_page'] = 'sign_up'


def show_homepage():

    #global user_data, user_id

    #if user_data is None:
    #    try:
    #        response = requests.get(base_url + "users/get_data", json={"U_Id": str(user_id)})
    #        response.raise_for_status()
    #        user_data = response.json()
    #    except requests.exceptions.RequestException as e:
    #        print(f"Error with login credentials: {e}")
    #    except json.JSONDecodeError:
    #        print("Error decoding JSON response.")

    st.title("Home Page")
    st.write(f"Welcome {st.session_state['user']['name']}!")
    if st.button("Log Out"):
        st.session_state['user'] = {}
        st.session_state['current_page'] = 'login'

    if st.button("Submit Survey"):
        st.session_state['current_page'] = 'survey'

    if st.button("View Catalog"):
        st.session_state['current_page'] = 'catalog'

    if st.button("View Account"):
        st.session_state['current_page'] = 'account'
    

def show_page_2():
    st.title("Page 2")
    st.write("This is the second page.")
    if st.button("Go back to Home"):
        st.session_state['current_page'] = 'home'

def show_sign_up():
    #global user_id
    st.title("Sign Up")
    st.write("Sign Up to Borrow or Purchase Books")
    name = st.text_input("Enter Name:")
    email = st.text_input("Enter Email:")
    password = st.text_input("Enter Password:")
    role_options = ["customer", "merchant"]
    selected_role = st.radio("Choose Role:", role_options)

    if st.button("Sign Up"):
        if (not name or not email or not password or not selected_role):
            st.error("Please fill in all fields")
        else:
            payload = {"name":str(name), "email": str(email), "password":str(password), "role":str(selected_role)}
            try:
                response = requests.post(base_url + "users", json=payload)
                response.raise_for_status()
                user_data = response.json()
                st.session_state["user"] = user_data
                print(f"USER DATA IN SIGN UP: {st.session_state['user']}")
                st.session_state['current_page'] = 'home'
            except requests.exceptions.RequestException as e:
                print(f"Error with Signing Up: {e}")
                st.error("Error with signing up")
            except json.JSONDecodeError:
                print("Error decoding JSON response.")
    
    if st.button("Already have an account? Log In."):
        st.session_state['current_page'] = 'login'

def show_survey():

    global user_id, user_data

    st.title("Survey")
    st.write("Submit Survey to Get Better Recommended Books")
    fav_author = st.text_input("Enter Favorite Author:")
    fav_genre = st.text_input("Enter Favorite Genre:")
    fav_book = st.text_input("Enter Favorite Book:")

    if st.button("Go Back"):
        st.session_state['current_page'] = 'home'
    
    if st.button("Submit Survey"):
        if (not fav_author or not fav_genre or not fav_book):
            st.error("Please fill in all fields")
        else:
            payload = {"c_id": str(st.session_state['user']['user_id']),"fav_authors": str(fav_author), "fav_genres": str(fav_genre), "fav_books": str(fav_book)}
            try:
                response = requests.put(base_url+f"users/{st.session_state['user']['user_id']}/preferences", json=payload)
                response.raise_for_status()
                st.write("Survey successfully submitted!")
                st.session_state['current_page'] = 'home'
            except requests.exceptions.RequestException as e:
                print(f"Error with Submitting Survey: {e}")
                st.error("Error with submitting survey")
            except json.JSONDecodeError:
                print("Error decoding JSON response.")

def show_catalog():

    st.title("Book Catalog")
    st.write("View our wide selection of books!")

    author = st.text_input("Enter Author to Filter By: Optional")
    genre = st.text_input("Enter Genre to Filter By: Optional")
    max_price = st.text_input("Enter Max Price to Filter By")

    if st.button("Go Back"):
        st.session_state['current_page'] = 'home'

    if st.button("View Filtered Books"):
        print(f"IN VIEW BOOKS")
        if (not max_price):
            max_price = "Infinity"

        if (not genre):
            genre = None
        if (not author):
            author = None
        
        try:
            payload = {"genre":genre, "author":author, "max_price":max_price}
            response = requests.post(base_url+f"books/filter", json=payload)
            response.raise_for_status()

            book_data = response.json()

            st.session_state['filtered'] = book_data
            st.session_state['current_page'] = 'filtered_books'
        except requests.exceptions.RequestException as e:
            print(f"Error with getting filtered books: {e}")
            st.error("Error with getting filtered books")
        except json.JSONDecodeError:
            print("Error decoding JSON response.")



def show_account():

    st.title("Account Page")
    st.write("View your account details")

    if st.button("Go Back"):
        st.session_state['current_page'] = 'home'
    
    if st.button("View Transaction History"):
        st.session_state['current_page'] = 'transaction'

    if st.button("Delete Account"):
        try:
            response = requests.delete(base_url+f"users/{st.session_state['user']['user_id']}", json={'user_id':st.session_state['user']['user_id']})
            response.raise_for_status()
            st.info("Account Deleted!")
            st.session_state['user'] = {}
            st.session_state['current_page'] = 'login'
        except requests.exceptions.RequestException as e:
            print(f"Error with Deleting Account: {e}")
            st.error("Error with Deleting Account")
        except json.JSONDecodeError:
            print("Error decoding JSON response.")
    
    if st.button("View Recommended Books"):
        st.session_state['current_page'] = 'recommended'

def show_transaction_history():
    st.title("Transaction History")

    try:
        response = requests.get(base_url+f"transactions/{st.session_state['user']['user_id']}", json={'user_id':st.session_state['user']['user_id']})
        response.raise_for_status()

        transaction_data = response.json()

        if transaction_data:
            for index, transaction in enumerate(transaction_data):
                col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 2, 2, 3, 2, 3, 3])
                with col1:
                    st.subheader(transaction.get("transaction\_id", str(index)))
                with col2:
                    st.write(f"**Title:** {transaction.get('book_title', 'N/A')}")

                with col3:
                    st.write(f"**Genre:** {transaction.get('genre', 'N/A')}")
                with col4:
                    st.write(f"**Date:** {transaction.get('date', 'N/A')}")
                with col5:
                    st.write(f"**Due Date:** {transaction.get('due_date', 'N/A')}")
                with col6:
                    st.write(f"**Borrowable:** {transaction.get('is_library', 'N/A')}")
                with col7:
                    st.write(f"**Returned At:** {transaction.get('returned_at', 'N/A')}")
        else:
            st.write("No transaction history to display")

    except requests.exceptions.RequestException as e:
        print(f"Error with Getting Transaction History: {e}")
        st.error("Error with Getting Transaction History")
    except json.JSONDecodeError:
        print("Error decoding JSON response.")

    if st.button("View Overdue Books"):
        st.session_state['current_page'] = 'overdue'

    if st.button("View Total Fines"):
        st.session_state['current_page'] = 'fines'

    if st.button("Go Back"):
        st.session_state['current_page'] = 'account'


def show_overdue_books():

    st.title("Overdue Books")

    try:
        # make sure overdue api takes into account that book is not returned yet
        response = requests.get(base_url+f"transactions/{st.session_state['user']['user_id']}/overdue", json={"user_id": st.session_state['user']['user_id']})
        response.raise_for_status()
        overdue_data = response.json()

        if overdue_data:
            for transaction in overdue_data:
                col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])
                with col1:
                    st.subheader(transaction.get("transaction_id", "No ID"))

                with col2:
                    st.write(f"**Title:** {transaction.get('book_title', 'N/A')}")

                with col3:
                    st.write(f"**Borrowed On:** {transaction.get('borrowed_on', 'N/A')}")
                with col4:
                    st.write(f"**Due Date:** {transaction.get('due_date', 'N/A')}")
        else:
            st.write("No overdue books to display")

    except requests.exceptions.RequestException as e:
        print(f"Error with Getting Overdue Books: {e}")
        st.error("Error with Getting Overdue Books")
    except json.JSONDecodeError:
        print("Error decoding JSON response.")


    if st.button("Return Books"):
        # Return books logic
        # Make sure api updates returned _at for the books

        try:
            for book in overdue_data:
                response = requests.put(base_url+f"transactions/{book.get('transaction_id')}/return", json={"transaction_id": book.get('transaction_id')})
                response.raise_for_status()
                return_response = response.json()

            st.info("Overdue Books Successfully Returned")
        except requests.exceptions.RequestException as e:
            print(f"Error with Returning Books: {e}")
            st.error("Error with Returning Books")
        except json.JSONDecodeError:
            print("Error decoding JSON response.")

    if st.button("Go Back"):
        st.session_state['current_page'] = 'transaction'

def show_fines():
    st.title("View Fines")
    
    # Get fines
    try:
        response = requests.get(base_url+f"transactions/{st.session_state['user']['user_id']}/total_fines", json={'user_id':st.session_state['user']['user_id']})
        response.raise_for_status()

        total_fines = response.json()

        st.write(f"Total Fines are ${total_fines['fine']}")

    except requests.exceptions.RequestException as e:
        print(f"Error with Getting Fines: {e}")
        st.error("Error with Getting Fines")
    except json.JSONDecodeError:
        print("Error decoding JSON response.")

    if st.button("Go Back"):
        st.session_state['current_page'] = 'account'


def show_purchase():
    st.title("Purchase Page")
    st.write(f"You are purchasing {st.session_state['purchase']['title']} for {st.session_state['purchase']['price']}")

    if st.button("Purchase"):
        # Call transaction API

        try:
        # Create transaction
            print(f"Purchase book id: {st.session_state['purchase']['id']}")
            payload = {"b_id":st.session_state['purchase']['id'], "c_id":str(st.session_state['user']['user_id'])}
            response = requests.post(base_url+"/transactions", json=payload)
            response.raise_for_status()
            # Update Stock
            # Call api to update stock

            st.info("Transaction successfully completed")
        except requests.exceptions.RequestException as e:
            print(f"Error with Creating Transaction: {e}")
            st.error("Book is Out of Stock")
        except json.JSONDecodeError:
            print("Error decoding JSON response.")
        st.session_state['purchase'] = {}
        st.session_state['current_page'] = 'catalog'
    if st.button("Go Back"):
        st.session_state['purchase'] = {}
        st.session_state['current_page'] = 'catalog'


def show_filtered():
    st.title("Filtered Books")

    book_data = st.session_state['filtered']

    if book_data:
        selected_book_id = st.radio("Select a book to purchase",
                                    [book.get("id") for book in book_data],
                                    format_func=lambda book_id: next((b.get("title", "No Title") for b in book_data if b.get("id") == book_id), "Unknown Book"))

        st.write("---")
        st.subheader("Book Details:")
        selected_book = next((book for book in book_data if book.get("id") == selected_book_id), None)

        if selected_book:
            col1, col2, col3, col4 = st.columns(4)
            col1.write(f"**Title:** {selected_book.get('title', 'No Title')}")
            col2.write(f"**Genre:** {selected_book.get('genre', 'N/A')}")
            col3.write(f"**Price:** ${selected_book.get('price', 'N/A')}")
            rating = selected_book.get('rating')
            col4.write(f"**Rating:** {rating}/5" if rating is not None else "**Rating:** N/A")

            # If purchase button comes here
            if st.button("Purchase Selected Book"):
                print("PURCHASE BUTTON")
                st.session_state['purchase'] = selected_book
                st.session_state['current_page'] = 'purchase'

                #if (st.session_state[f"purchase_clicked_{book.get('id')}"]):
                #    del st.session_state[f"purchase_clicked_{book.get('id')}"]
                #    try:
                #        # Create transaction
                #        payload = {"b_id":book.get('id'), "c_id":str(st.session_state['user']['user_id'])}
                #        response = requests.post(base_url+"/transactions", json=payload)
                #        response.raise_for_status()

                        # Update Stock
                        # Call api to update stock

                #       st.info("Transaction successfully completed")
                #    except requests.exceptions.RequestException as e:
                #        print(f"Error with Creating Transaction: {e}")
                #        st.error("Error with Performing Transaction")
                #    except json.JSONDecodeError:
                #        print("Error decoding JSON response.")
    else:
        st.info("No book data available.")

    if st.button("Go Back"):
        st.session_state['filtered'] = {}
        st.session_state['current_page'] = 'catalog'


def show_recommended():
    st.title("Recommended Books")

    try:
        response_rec = requests.get(base_url+f"books/recommend/{st.session_state['user']['user_id']}", json={"user_id":st.session_state['user']['user_id']})
        response_rec.raise_for_status()
        book_data_recommended = response_rec.json()


        if book_data_recommended:
            for book_rec in book_data_recommended:
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])  # Adjust column widths as needed


                with col1:
                    st.subheader(book_rec.get("title", "No Title"))


                with col2:
                    st.write(f"**Genre:** {book_rec.get('genre', 'N/A')}")


                with col3:
                    st.write(f"**Price:** ${book_rec.get('price', 'N/A')}")


                with col4:
                    rating = book_rec.get('rating')
                    if rating is not None:
                        st.write(f"**Rating:** {rating}/5")
                    else:
                        st.write("**Rating:** N/A")
        else:
            st.info("No book data available.")
    except requests.exceptions.RequestException as e:
        print(f"Error with getting filtered books: {e}")
        st.error("Error with getting recommended books")
    except json.JSONDecodeError:
        print("Error decoding JSON response.")

    if st.button("Go Back"):
        st.session_state['current_page'] = 'account'


#if st.session_state['current_page'] == 'home':
#    show_homepage()
#elif st.session_state['current_page'] == 'page_2':
#    show_page_2()


if __name__ == '__main__':
    base_url = "http://127.0.0.1:5000/"
    user_data = None
    user_id = None

    if "user" not in st.session_state:
        st.session_state["user"] = {}

    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = 'login'

    if "purchase" not in st.session_state:
        st.session_state["purchase"] = {}

    if "filtered" not in st.session_state:
        st.session_state['filtered'] = {}

    print(f"REFRESHING: current page is {st.session_state['current_page']}")

    if st.session_state['current_page'] == 'login':
        show_login()
    elif st.session_state['current_page'] == 'home':
        show_homepage()
    elif st.session_state['current_page'] == 'sign_up':
        show_sign_up()
    elif st.session_state['current_page'] == 'survey':
        show_survey()
    elif st.session_state['current_page'] == 'catalog':
        show_catalog()
    elif st.session_state['current_page'] == 'account':
        show_account()
    elif st.session_state['current_page'] == 'transaction':
        show_transaction_history()
    elif st.session_state['current_page'] == 'overdue':
        show_overdue_books()
    elif st.session_state['current_page'] == 'fines':
        show_fines()
    elif st.session_state['current_page'] == 'purchase':
        show_purchase()
    elif st.session_state['current_page'] == 'filtered_books':
        show_filtered()
    elif st.session_state['current_page'] == 'recommended':
        show_recommended()